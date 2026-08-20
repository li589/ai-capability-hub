# FoloToy Web App API Workflow

Use this reference only after reading the safety model in `SKILL.md`.

## Service selection

Choose the service that matches the user's account region:

```text
Mainland China: https://webapp.folotoy.cn
International:  https://webapp.folotoy.com
```

Use `Content-Type: application/json`. After sign-in, send the access token as:

```http
Authorization: Bearer ACCESS_TOKEN
```

Keep the token out of files, URLs, screenshots, logs, and final output.

## 1. Request an SMS code

```http
POST /v1/verification/token
Content-Type: application/json

{
  "identifier": "+COUNTRY_CODE_PHONE_NUMBER"
}
```

Wait for the user to provide the six-digit code.

## 2. Sign in

```http
POST /v1/auth/signin
Content-Type: application/json

{
  "username": "+COUNTRY_CODE_PHONE_NUMBER",
  "verification_token": "RUNTIME_SIX_DIGIT_CODE",
  "accept_terms": true
}
```

The response contains an `access_token`. Keep it only for the active task.

## 3. Check pairing state

```http
GET /v1/toys/sn/{sn}/paired
```

Do not pair until the user confirms ownership or authorization.

## 4. Pair when required

```http
POST /v1/toys/pair
Content-Type: application/json
Authorization: Bearer ACCESS_TOKEN

{
  "sn": "RUNTIME_DEVICE_SN",
  "password": "RUNTIME_PAIRING_KEY"
}
```

Stop if the device is already paired to another account.

## 5. Resolve device and character

```http
GET /v1/toys
GET /v1/toys/{toy_id}
GET /v1/toys/{toy_id}/characters
```

Resolve the target by its exact SN. Record the `toy_id`, `product_id`, active character ID, online state, and complete current character object.

## 6. Read available models

```http
GET /v1/models?mod_type=stt&product_id={product_id}
GET /v1/models?mod_type=llm&product_id={product_id}
GET /v1/models?mod_type=tts&product_id={product_id}
```

Use the TTS response to map `text_to_speech_id` values to readable voice names. The production workflow uses `/v1/models`; do not depend on legacy `/v1/voices` routes.

## 7. Preview the proposed update

The configurable fields are normally:

| User concept | Character field |
| --- | --- |
| Persona and behavior | `custom_ability` |
| Opening line | `start_text` |
| Voice | `text_to_speech_id` |

Display the current and proposed values and obtain explicit confirmation.

## 8. Update the character

```http
PUT /v1/toys/{toy_id}/characters/{character_id}
Content-Type: application/json
Authorization: Bearer ACCESS_TOKEN

COMPLETE_MERGED_CHARACTER_OBJECT
```

Build the request from the complete object returned by the character endpoint. Replace only confirmed fields. Preserve `speech_to_text_id`, `language_model_id`, and every other required or product-specific value.

## 9. Verify

```http
GET /v1/toys/{toy_id}/characters
GET /v1/toys/{toy_id}
```

Verify exact read-back values and map the saved TTS ID to the readable voice name. Then guide a new physical-device conversation.

## Common errors

| Situation | Response |
| --- | --- |
| SMS not received | Verify the country code, wait for the resend timer, and avoid repeated sends. |
| `401` or `403` | Treat the token as expired and sign in again. |
| Device paired elsewhere | Stop; use the supported ownership/unpairing flow. |
| Voice route returns `404` | Use `/v1/models?mod_type=tts&product_id=...`. |
| Content review error such as `10500` | Shorten and simplify the affected text; do not overwrite the current character until the new draft is approved. |
| Saved values are not audible | Verify the active character, online state, and a newly started conversation. |
