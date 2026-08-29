from app.services.intelligence.reasoning import (
    ReasoningResult,
)


class AnswerComposer:

    def compose(
        self,
        reasoning: ReasoningResult,
    ) -> str:

        answer = reasoning.answer.strip()

        if not answer:
            return (
                "Не удалось сформировать ответ "
                "на основе доступных данных."
            )

        return answer
