---
description: ONLY run when the user explicitly types the `/log-input` slash command. Do NOT invoke automatically for normal user messages. When explicitly invoked, record the user's input to ./input_log/<YYYY-MM-DD>-input-prompt.log as a JSON entry, then respond.
argument-hint: <text to log>
---

You have been invoked via the `/log-input` slash command. The user's input to log is:

$ARGUMENTS

Do the following, in order:

1. Get the current local date and time with: `date +'%Y-%m-%d %H:%M:%S'`. Parse it into `DATE` (YYYY-MM-DD) and `TIMESTAMP` (full YYYY-MM-DD HH:MM:SS).

2. Ensure the log directory exists relative to the current working directory: `mkdir -p ./input_log`.

3. Formulate your response to the user's input first, internally. Then extract the **first ten words** of that response (split on whitespace, take the first 10 tokens, join with single spaces). This is `response_preview`.

4. Append a single JSON line to `./input_log/<DATE>-input-prompt.log` with this exact shape:

   ```json
   {"timestamp": "<TIMESTAMP>", "input": "<the user's input from $ARGUMENTS, verbatim>", "response_preview": "<first ten words of your response>"}
   ```

   Use a heredoc or `jq -c -n` to ensure valid JSON escaping (especially for quotes/newlines in the input). Example with jq:

   ```bash
   jq -c -n --arg ts "$TIMESTAMP" --arg in "$ARGUMENTS" --arg rp "$RESPONSE_PREVIEW" \
     '{timestamp: $ts, input: $in, response_preview: $rp}' >> "./input_log/${DATE}-input-prompt.log"
   ```

5. After the log line is appended, reply to the user normally — your reply should begin with the same content you used to derive `response_preview` (so the recorded preview matches what the user actually sees).

Notes:
- If `$ARGUMENTS` is empty, tell the user the command requires input and do not write a log line.
- Do not log anything other than this single JSON line per invocation.
- Do not summarize or paraphrase the user's input when writing it to the log — store it verbatim.
