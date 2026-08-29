"use client";

import {
  FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";

type Citation = {
  url: string;
  title: string | null;
};

type Fact = {
  claim: string;
  value: number | null;
  unit: string | null;
  period: string | null;
  verified: boolean;
};

type IntelligenceResponse = {
  answer: string;
  verified: boolean;
  confidence: number;
  citations: Citation[];
  warnings: string[];
  facts: Fact[];
};

type ThinkingStep = {
  id: string;
  label: string;
  status: "pending" | "active" | "complete";
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  facts?: Fact[];
};

type Chat = {
  id: string;
  title: string;
  messages: ChatMessage[];
  updatedAt: number;
};

const STORAGE_KEY = "veyra-chats";

function createChat(): Chat {
  return {
    id: crypto.randomUUID(),
    title: "New conversation",
    messages: [],
    updatedAt: Date.now(),
  };
}

export default function Home() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] =
    useState<string | null>(null);

  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const [thinkingSteps, setThinkingSteps] =
    useState<ThinkingStep[]>([]);

  const [thinkingExpanded, setThinkingExpanded] =
    useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(
        STORAGE_KEY
      );

      if (stored) {
        const parsed = JSON.parse(stored) as Chat[];

        if (parsed.length > 0) {
          setChats(parsed);
          setActiveChatId(parsed[0].id);
          setReady(true);
          return;
        }
      }
    } catch (error) {
      console.error(
        "Failed to restore chats:",
        error
      );
    }

    const initialChat = createChat();

    setChats([initialChat]);
    setActiveChatId(initialChat.id);
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;

    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(chats)
    );
  }, [chats, ready]);

  const activeChat = useMemo(
    () =>
      chats.find(
        (chat) => chat.id === activeChatId
      ) ?? null,
    [chats, activeChatId]
  );

  function createNewChat() {
    const chat = createChat();

    setChats((current) => [
      chat,
      ...current,
    ]);

    setActiveChatId(chat.id);
    setQuery("");
  }

  function updateChat(
    chatId: string,
    updater: (chat: Chat) => Chat
  ) {
    setChats((current) =>
      current.map((chat) =>
        chat.id === chatId
          ? updater(chat)
          : chat
      )
    );
  }

  async function submitQuery(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const text = query.trim();

    if (!text || loading || !activeChatId) {
      return;
    }

    const chatId = activeChatId;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    };

    const assistantMessageId =
      crypto.randomUUID();

    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
    };

    updateChat(chatId, (chat) => ({
      ...chat,
      title:
        chat.messages.length === 0
          ? text.length > 42
            ? `${text.slice(0, 42)}…`
            : text
          : chat.title,
      messages: [
        ...chat.messages,
        userMessage,
        assistantMessage,
      ],
      updatedAt: Date.now(),
    }));

    setQuery("");
    setLoading(true);
    setThinkingSteps([]);
    setThinkingExpanded(true);

    try {
      const response = await fetch(
        "http://localhost:8000/api/intelligence/query/stream",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },
          body: JSON.stringify({
            query: text,
            has_workspace: false,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `API error: ${response.status}`
        );
      }

      if (!response.body) {
        throw new Error(
          "Streaming response body is unavailable."
        );
      }

      const reader =
        response.body.getReader();

      const decoder =
        new TextDecoder();

      let buffer = "";
      let accumulated = "";

      const updateAssistant = (
        content: string
      ) => {
        updateChat(chatId, (chat) => ({
          ...chat,
          messages: chat.messages.map(
            (message) =>
              message.id === assistantMessageId
                ? {
                    ...message,
                    content,
                  }
                : message
          ),
          updatedAt: Date.now(),
        }));
      };

      const handleThinkingEvent = (
        event: {
          type?: string;
          status?: string;
          label?: string;
          count?: number;
        }
      ) => {
        const stepMap: Record<string, string> = {
          research_started: "Изучаю запрос",
          search_started: "Ищу актуальные данные",
          verification_started: "Сверяю показатели",
          reasoning_started: "Формирую ответ",
        };

        if (event.type === "sources_found") {
          setThinkingSteps((current) => {
            const completed = current.map((step) => ({
              ...step,
              status:
                step.status === "active"
                  ? "complete"
                  : step.status,
            }));

            return [
              ...completed,
              {
                id: "sources_found",
                label:
                  event.label ||
                  `Нашла ${event.count ?? 0} источников`,
                status: "complete",
              },
            ];
          });

          return;
        }

        if (event.type === "completed") {
          setThinkingSteps((current) =>
            current.map((step) => ({
              ...step,
              status: "complete",
            }))
          );

          setThinkingExpanded(false);
          return;
        }

        const label =
          event.type
            ? stepMap[event.type]
            : undefined;

        if (!label) {
          return;
        }

        setThinkingSteps((current) => {
          const completed = current.map((step) => ({
            ...step,
            status:
              step.status === "active"
                ? "complete"
                : step.status,
          }));

          return [
            ...completed,
            {
              id: event.type!,
              label,
              status: "active",
            },
          ];
        });
      };

      const processEvent = (
        rawEvent: string
      ) => {
        const dataLines = rawEvent
          .split("\n")
          .filter((line) =>
            line.startsWith("data:")
          );

        if (!dataLines.length) {
          return;
        }

        const payload = dataLines
          .map((line) =>
            line.slice(5).trim()
          )
          .join("\n");

        if (!payload) {
          return;
        }

        let event: {
          type?: string;
          content?: string;
          message?: string;
          citations?: {
            url: string;
            title?: string | null;
          }[];
          facts?: Fact[];
        };

        try {
          event = JSON.parse(payload);
        } catch {
          console.warn(
            "Invalid SSE event:",
            payload
          );
          return;
        }

        handleThinkingEvent(event);

        if (event.type === "answer") {
          accumulated =
            event.content || "";

          updateChat(chatId, (chat) => ({
            ...chat,
            messages: chat.messages.map(
              (message) =>
                message.id ===
                assistantMessageId
                  ? {
                      ...message,
                      content: accumulated,
                      citations:
                        event.citations?.map(
                          (citation) => ({
                            url: citation.url,
                            title:
                              citation.title ?? null,
                          })
                        ),
                      facts:
                        event.facts,
                    }
                  : message
            ),
            updatedAt: Date.now(),
          }));

          return;
        }

        if (event.type === "error") {
          updateAssistant(
            event.message ||
              "Не удалось получить ответ от Veyra."
          );
        }
      };

      while (true) {
        const { value, done } =
          await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(
          value,
          {
            stream: true,
          }
        );

        const events =
          buffer.split("\n\n");

        buffer =
          events.pop() || "";

        for (const event of events) {
          processEvent(event);
        }
      }

      buffer += decoder.decode();

      if (buffer.trim()) {
        processEvent(buffer);
      }

      if (!accumulated) {
        updateAssistant(
          "Не удалось сформировать ответ."
        );
      }
    } catch (error) {
      console.error(error);

      updateChat(chatId, (chat) => ({
        ...chat,
        messages: chat.messages.map(
          (message) =>
            message.id === assistantMessageId
              ? {
                  ...message,
                  content:
                    "Не удалось получить ответ от Veyra. Проверьте подключение к серверу.",
                }
              : message
        ),
        updatedAt: Date.now(),
      }));
    } finally {
      setLoading(false);
    }
  }

  if (!ready) {
    return (
      <main className="flex h-screen items-center justify-center bg-[#f3f5f7]">
        <div className="text-sm text-black/40">
          Veyra
        </div>
      </main>
    );
  }

  return (
    <main className="relative flex h-screen overflow-hidden bg-[#f3f5f7] text-[#18181b]">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-white/70 blur-3xl" />
        <div className="absolute right-[-80px] top-[15%] h-96 w-96 rounded-full bg-white/60 blur-3xl" />
        <div className="absolute bottom-[-120px] left-[35%] h-80 w-80 rounded-full bg-white/50 blur-3xl" />
      </div>

      {/* SIDEBAR */}
      <aside
        className={[
          "relative z-20 shrink-0 overflow-hidden border-r border-white/70",
          "bg-white/45 backdrop-blur-2xl backdrop-saturate-150",
          "shadow-[0_0_40px_rgba(20,30,40,0.04)]",
          "transition-all duration-300",
          sidebarOpen
            ? "w-[280px]"
            : "w-0 border-r-0",
        ].join(" ")}
      >
        <div className="flex h-full w-[280px] flex-col px-3 py-3">
          {/* Brand */}
          <div className="flex items-center justify-between px-2 py-2">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#171717] text-sm font-semibold text-white">
                V
              </div>

              <div className="text-sm font-semibold">
                Veyra
              </div>
            </div>

            <button
              onClick={() =>
                setSidebarOpen(false)
              }
              className="rounded-lg px-2 py-1 text-black/40 transition hover:bg-white/70 hover:text-black"
              aria-label="Close sidebar"
            >
              ‹
            </button>
          </div>

          {/* New chat */}
          <button
            onClick={createNewChat}
            className="mt-2 flex w-full items-center gap-3 rounded-xl border border-white/70 bg-white/45 px-3 py-2.5 text-left text-sm font-medium shadow-sm backdrop-blur-xl transition hover:bg-white/75"
          >
            <span className="text-base">＋</span>
            New chat
          </button>

          {/* Search */}
          <div className="mt-3 rounded-xl border border-white/70 bg-white/35 px-3 py-2.5 backdrop-blur-xl">
            <div className="flex items-center gap-2 text-sm text-black/40">
              <span>⌕</span>
              <span>Search</span>
              <span className="ml-auto text-[10px] text-black/25">
                ⌘ K
              </span>
            </div>
          </div>

          {/* Navigation */}
          <div className="mt-5 space-y-1">
            <div className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-black/30">
              Workspace
            </div>

            <button className="flex w-full items-center gap-3 rounded-xl bg-white/55 px-3 py-2.5 text-left text-sm font-medium text-black/75 shadow-sm">
              <span className="text-[15px]">
                ◷
              </span>
              Chats
            </button>

            <button className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-black/55 transition hover:bg-white/55">
              <span className="text-[15px]">
                ▱
              </span>
              Library
            </button>

            <button className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-black/55 transition hover:bg-white/55">
              <span className="text-[15px]">
                ▦
              </span>
              Projects
            </button>
          </div>

          {/* Recent chats */}
          <div className="mt-6 min-h-0 flex-1 overflow-y-auto">
            <div className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-black/30">
              Recent chats
            </div>

            <div className="space-y-1">
              {chats
                .slice()
                .sort(
                  (a, b) =>
                    b.updatedAt -
                    a.updatedAt
                )
                .map((chat) => (
                  <button
                    key={chat.id}
                    onClick={() => {
                      setActiveChatId(chat.id);
                      setQuery("");
                    }}
                    className={[
                      "w-full truncate rounded-xl px-3 py-2.5 text-left text-[13px] transition",
                      chat.id === activeChatId
                        ? "bg-white/65 text-black/75 shadow-sm"
                        : "text-black/55 hover:bg-white/55",
                    ].join(" ")}
                  >
                    {chat.title}
                  </button>
                ))}
            </div>
          </div>

          {/* Account */}
          <div className="border-t border-white/60 pt-3">
            <button className="flex w-full items-center gap-3 rounded-2xl border border-white/70 bg-white/35 p-2.5 text-left backdrop-blur-xl transition hover:bg-white/65">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#202020] text-xs font-semibold text-white">
                N
              </div>

              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">
                  Nikita
                </div>

                <div className="truncate text-[11px] text-black/40">
                  Personal workspace
                </div>
              </div>

              <span className="text-sm text-black/30">
                ⋯
              </span>
            </button>
          </div>
        </div>
      </aside>

      {/* MAIN */}
      <section className="relative z-10 flex min-w-0 flex-1 flex-col">
        <header className="relative z-20 flex h-14 shrink-0 items-center border-b border-white/70 bg-white/35 px-4 backdrop-blur-2xl backdrop-saturate-150">
          {!sidebarOpen && (
            <button
              onClick={() =>
                setSidebarOpen(true)
              }
              className="mr-3 rounded-xl border border-white/80 bg-white/55 px-2.5 py-1.5 text-sm text-black/55 shadow-sm backdrop-blur-xl transition hover:bg-white/80"
              aria-label="Open sidebar"
            >
              ☰
            </button>
          )}

          <div className="truncate text-sm font-medium">
            {activeChat?.title ??
              "New conversation"}
          </div>

          <div className="ml-auto hidden items-center gap-2 text-[11px] text-black/40 sm:flex">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            Intelligence online
          </div>
        </header>

        {/* Conversation */}
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-[860px] px-5 pb-44 pt-10">
            {!activeChat ||
              (activeChat.messages.length === 0 &&
                !loading && (
                  <div className="flex min-h-[65vh] flex-col items-center justify-center text-center">
                    <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/80 bg-white/60 text-xl font-semibold shadow-lg backdrop-blur-xl">
                      V
                    </div>

                    <h1 className="text-4xl font-semibold tracking-[-0.04em] sm:text-5xl">
                      What should we research?
                    </h1>

                    <p className="mt-4 max-w-lg text-[15px] leading-6 text-black/45">
                      Markets, economics,
                      companies, crypto,
                      liquidity and financial
                      intelligence.
                    </p>
                  </div>
                ))}

            {activeChat?.messages.map(
              (message) => (
                <article
                  key={message.id}
                  className="mb-9 max-w-3xl"
                >
                  {message.role ===
                  "user" ? (
                    <>
                      <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-black/35">
                        You
                      </div>

                      <div className="text-[17px] leading-8">
                        {message.content}
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="mb-3 flex items-center gap-2">
                        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#171717] text-[11px] font-semibold text-white">
                          V
                        </div>

                        <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-black/35">
                          Veyra
                        </div>
                      </div>

                      <div className="whitespace-pre-wrap text-[15px] leading-8 text-black/80">
                        {message.content}
                      </div>

                      {message.facts &&
                        message.facts.length >
                          0 && (
                          <div className="mt-7 space-y-3">
                            {message.facts.map(
                              (
                                fact,
                                index
                              ) => (
                                <div
                                  key={`${fact.claim}-${index}`}
                                  className="rounded-2xl border border-white/80 bg-white/50 p-5 shadow-sm backdrop-blur-xl"
                                >
                                  <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-black/35">
                                    Key fact
                                  </div>

                                  <div className="mt-2 text-2xl font-semibold tracking-tight">
                                    {fact.value ??
                                      "—"}
                                    {fact.unit ??
                                      ""}
                                  </div>

                                  <div className="mt-2 text-[13px] leading-5 text-black/50">
                                    {fact.claim}
                                  </div>
                                </div>
                              )
                            )}
                          </div>
                        )}

                      {message.citations &&
                        message.citations.length >
                          0 && (
                          <div className="mt-7">
                            <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-black/35">
                              Sources
                            </div>

                            <div className="flex flex-wrap gap-2">
                              {message.citations.map(
                                (
                                  citation,
                                  index
                                ) => (
                                  <a
                                    key={`${citation.url}-${index}`}
                                    href={
                                      citation.url
                                    }
                                    target="_blank"
                                    rel="noreferrer"
                                    className="max-w-full truncate rounded-full border border-white/85 bg-white/55 px-3 py-1.5 text-[11px] text-black/55 shadow-sm backdrop-blur-xl transition hover:bg-white/80"
                                  >
                                    {citation.title ||
                                      new URL(
                                        citation.url
                                      ).hostname}
                                  </a>
                                )
                              )}
                            </div>
                          </div>
                        )}
                    </>
                  )}
                </article>
              )
            )}

            {loading && (
              <div className="max-w-xl">
                <div className="mb-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-black/35">
                  Veyra
                </div>

                <div className="rounded-3xl border border-white/80 bg-white/50 p-5 shadow-sm backdrop-blur-xl">
                  <div className="space-y-3 text-sm text-black/45">
                    {[
                      "Searching sources…",
                      "Checking evidence…",
                      "Building answer…",
                    ].map((item) => (
                      <div
                        key={item}
                        className="flex items-center gap-3"
                      >
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-black/35" />
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Composer */}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 z-30 px-4 pb-4 pt-12">
          <form
            onSubmit={submitQuery}
            className="pointer-events-auto mx-auto max-w-[860px]"
          >
            <div className="rounded-[26px] border border-white/85 bg-white/65 p-2 shadow-[0_16px_50px_rgba(20,30,40,0.10)] backdrop-blur-2xl backdrop-saturate-150">
              <textarea
                value={query}
                onChange={(event) =>
                  setQuery(event.target.value)
                }
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" &&
                    !event.shiftKey
                  ) {
                    event.preventDefault();

                    if (!loading) {
                      event.currentTarget.form?.requestSubmit();
                    }
                  }
                }}
                rows={1}
                placeholder="Ask Veyra anything about finance…"
                className="min-h-[48px] w-full resize-none bg-transparent px-4 py-3 text-[14px] outline-none placeholder:text-black/35"
              />

              <div className="flex items-center justify-between px-3 pb-1">
                <div className="text-[10px] text-black/35">
                  Enter to send · Shift + Enter
                  for new line
                </div>

                <button
                  type="submit"
                  disabled={
                    loading ||
                    !query.trim()
                  }
                  className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#171717] text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-[#303030] disabled:cursor-not-allowed disabled:bg-black/15"
                  aria-label="Send"
                >
                  ↑
                </button>
              </div>
            </div>

            <div className="mt-2 text-center text-[10px] leading-4 text-black/35">
              Veyra может допускать ошибки.
              Проверяйте важную информацию по
              первоисточникам. 100% точность не
              гарантируется.
            </div>
          </form>
        </div>
      </section>
    </main>
  );
}
