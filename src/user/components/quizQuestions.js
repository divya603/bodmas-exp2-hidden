// Comprehension quiz shown after the instructions (design.js). All questions
// must be answered correctly; otherwise the participant returns to the
// instructions. Question 3 checks the reason to answer NO that practice item P2
// teaches: a different mistake. (Experiment 1's question 4, on a problem with no
// brackets and a brackets statement, was removed on 2026-09-14 at the user's
// request. Since 2026-09-16 the task answer is YES / NO, not a rating.)
export const QUIZ_QUESTIONS = [
  {
    id: 'pg1',
    questions: [
      {
        id: 'q1',
        question: 'What should your answer be based on?',
        multiSelect: false,
        answers: [
          "How well the statement explains the student's work",
          'Whether the final answer is correct',
          'How many steps the student used',
          'How long the problem is',
        ],
        correctAnswer: ["How well the statement explains the student's work"],
      },
      {
        id: 'q2',
        question: 'How many mistakes does each student make?',
        multiSelect: false,
        answers: ['Exactly one', 'None', 'Two', 'It varies'],
        correctAnswer: ['Exactly one'],
      },
      {
        id: 'q3',
        question:
          "A student's mistake is doing subtraction before multiplication. The statement says the student believes " +
          'addition should be done before multiplication. Should you answer YES or NO?',
        multiSelect: false,
        answers: ['YES', 'NO'],
        correctAnswer: ['NO'],
      },
    ],
  },
]
