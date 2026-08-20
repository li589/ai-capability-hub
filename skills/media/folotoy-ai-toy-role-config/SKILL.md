---
name: folotoy-ai-toy-role-config
description: Configure a FoloToy AI toy with TRAE Work or other AI tools through the FoloToy Web App. Use this general-purpose skill to read and set an authorized toy's persona, voice, and opening line, preview changes before writing, and verify the saved configuration through API read-back and a physical-device test.
---

# FoloToy AI Toy Role Configuration

Use TRAE Work or another compatible AI tool to safely configure a FoloToy AI toy's persona, voice, and opening line, then verify the result on the physical device.

Read [references/api-workflow.md](references/api-workflow.md) before making API calls. Read [references/examples.md](references/examples.md) when the user wants help designing a persona or opening line.

## Supported tasks

- Sign in with a phone number and a one-time SMS code.
- Check whether an authorized device is already paired.
- Pair an unpaired device with its SN and pairing key.
- Read the current device, active character, and available voice models.
- Change the character persona, opening line, and voice.
- Read the saved character back and guide a physical-device test.

Do not use this skill to unpair a device, erase memory, reset networking, delete an account, purchase services, or control a device the user does not own or have explicit authorization to manage.

## Safety model

Secrets identify an account or physical device. Keep them out of prompts, source files, screenshots, URLs, persistent logs, and final reports.

1. Ask for the phone number, SMS code, SN, and pairing key only when each value is needed.
2. Do not echo a complete phone number, SMS code, pairing key, or access token.
3. Keep the access token only for the current task. Prefer an in-memory variable or a protected temporary session and remove it when finished.
4. Stop when ownership is unclear or the device is paired to another account.
5. Show a human-readable diff and obtain explicit confirmation before the update request.
6. Change only the approved fields. Preserve the current model IDs and every other required field.
7. Read the character back after saving. A successful write response alone is not sufficient verification.

## Workflow

### 1. Establish region and consent

Ask whether the account uses Mainland China or the international service:

- Mainland China: `https://webapp.folotoy.cn`
- International: `https://webapp.folotoy.com`

Explain that the workflow sends one SMS and changes a physical device configuration. Confirm that the user owns the device or is authorized to manage it.

### 2. Sign in

Ask for the phone number including country code. Send the verification code using the request documented in the API reference.

Pause and ask for the six-digit code. Do not guess it, retrieve it from another source, or continue before the user supplies it.

Sign in and retain the returned bearer token only for this task. If authentication fails, verify the country code and code expiry. Do not repeatedly send SMS messages.

### 3. Resolve the target device

Ask for the device SN and check its pairing state.

- If it is already paired to the current account, continue.
- If it is unpaired, ask for the pairing key and obtain confirmation before pairing.
- If it is paired elsewhere, stop and explain that the current owner must unpair it through the supported product flow.

Read the account's devices and identify the exact target by SN. Never select a device only because its display name looks familiar.

### 4. Read before designing

Read the device details, online state, product ID, active character, and complete current character object. Fetch the available TTS models for the product and map IDs to readable voice names.

Ask for the intended audience, scenario, personality, tone, response length, behavior rules, safety boundaries, and voice preference. If the user has only a rough idea, propose a concise draft instead of blocking.

If the user has no explicit custom brief, use a relevant baseline from [references/examples.md](references/examples.md) as inspiration, then adapt it to the user's audience, scenario, and preferences. Do not apply an example without first showing the proposed persona, voice direction, and opening line.

### 5. Preview the change

Show this compact preview:

```text
Device: [masked SN and display name]
Character: [name]

Persona:     current -> proposed
Opening line: current -> proposed
Voice:        current name -> proposed name

Unchanged: STT model, LLM model, memory, network, pairing, and all other fields
```

Ask: `Apply this change to the listed FoloToy device?`

Continue only after an explicit confirmation.

### 6. Apply safely

Start from the complete character object returned by the service. Merge only the approved persona, opening line, and voice ID. Preserve existing required values such as `speech_to_text_id`, `language_model_id`, and all other product-specific fields.

Send the full merged object to the character update endpoint. Do not send a guessed or minimal payload when the service expects the complete configuration.

### 7. Verify and test

Read the character list again and compare the returned `custom_ability`, `start_text`, and `text_to_speech_id` with the approved proposal. Map the voice ID back to its readable name.

Check that the device is online. Ask the user to start a new conversation and test:

1. The opening line.
2. One normal in-character scenario.
3. One safety or uncertainty boundary.

If the saved configuration is correct but the behavior has not changed, verify the active character and start a fresh conversation before changing more fields.

### 8. Report and clean up

Report the character name, final opening line, final voice name, read-back status, physical-test status, and one suggested next iteration. Mask the device identity and clear temporary authorization data.

## Failure handling

- SMS not received: verify the country code, wait for the resend timer, and avoid repeated sends.
- `401` or `403`: treat the session as expired and sign in again. Do not reuse the old token.
- Pairing rejected: verify the SN and pairing key; stop if the device belongs to another account.
- Voice route not found: use the product model endpoint with `mod_type=tts`; do not rely on legacy `/v1/voices` routes.
- Content review error such as `10500`: shorten and simplify the persona or opening line. Keep the current configuration intact until a new draft is approved.
- Saved but not audible: verify the active character, device online state, and a newly started conversation.

## Completion criteria

The task is complete only when:

- The target device was authorized and resolved by SN.
- No secret was embedded or displayed unmasked.
- The user explicitly approved the displayed diff.
- Only approved fields changed.
- The API read-back matches the proposal.
- The user received a physical test script, even if the device is temporarily offline.
