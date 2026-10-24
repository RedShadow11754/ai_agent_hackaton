/**
 * Five fictitious sample messages for demos and the five-case test report.
 *
 * HARD RULE 7: all demo data is invented. Only reserved domains (.test /
 * .example) and documentation IPs (192.0.2.0/24) may appear here - never a real
 * company, URL, credential, or phone number.
 */

export interface SampleMessage {
  id: string;
  /** Short label shown on the sample picker button. */
  label: string;
  /** Sender line as the user would see it. */
  sender: string;
  /** The message body to paste into the investigation form. */
  body: string;
  /** What the demo is meant to exercise. */
  expectation: string;
}

export const SAMPLE_MESSAGES: SampleMessage[] = [
  {
    id: "sample-01-credential-phish",
    label: "Password reset (lookalike domain)",
    sender: "IT Support <it-support@secure-login.test>",
    body: [
      "Dear user,",
      "",
      "Your account password expires today. You must reset it immediately or",
      "lose access to email and payroll.",
      "",
      "Reset now: hxxps://secure-login[.]test/portal/reset?user=analyst",
      "",
      "Thank you,",
      "IT Support",
    ].join("\n"),
    expectation: "Credential request + lookalike domain + urgency. Expect Elevated or High.",
  },
  {
    id: "sample-02-invoice-fraud",
    label: "Invoice payment change",
    sender: "Accounts <billing@payroll-update.example>",
    body: [
      "Hi,",
      "",
      "Please note we have changed our bank details for the open invoice.",
      "Kindly pay the attached invoice today and confirm the transfer.",
      "This is confidential - do not discuss it with anyone else.",
      "",
      "Thanks,",
      "Accounts Team",
    ].join("\n"),
    expectation: "Payment-change request + secrecy. Expect High with SEC-02 cited.",
  },
  {
    id: "sample-03-short-ambiguous",
    label: "Too short to assess",
    sender: "Unknown",
    body: "hi, is this you?",
    expectation: "Too little text: expect a clarification question, not an assessment.",
  },
  {
    id: "sample-04-ip-literal-link",
    label: "Link to an IP literal",
    sender: "Payroll <payroll@intranet.example>",
    body: [
      "Your payslip is ready.",
      "",
      "Download it here: hxxp://192.0.2.45/payslip.pdf",
      "",
      "Reply urgently if you cannot access it.",
    ].join("\n"),
    expectation: "IP-literal host + urgency. Structural analysis only; never fetched.",
  },
  {
    id: "sample-05-benign-internal",
    label: "Routine internal notice",
    sender: "HR Team <hr@hr-portal.example>",
    body: [
      "Reminder: the office will be closed on the public holiday next Monday.",
      "",
      "No action is needed. Details are on the HR portal as usual.",
    ].join("\n"),
    expectation: "Low / Inconclusive at most - never labelled 'safe' (hard rule 5).",
  },
];
