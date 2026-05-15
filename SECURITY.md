# Security Guide (Private to Public)

This project is safe to keep private and later publish publicly if you follow this checklist.

## Never Commit Secrets

Do not commit any of the following:

- `.env`
- API keys, tokens, private keys, certificates
- endpoint credentials
- personal machine paths or local credentials

`/.gitignore` is configured to ignore `.env` permanently and keep `.env.example` committed.

## Required Safe Files

- `.env` (local only, not committed)
- `.env.example` (committed, no real secrets)

## Public Release Checklist

1. Confirm `.env` is not tracked.
2. Confirm `.env.example` contains placeholders only.
3. Rotate any keys you used during development.
4. Verify no secrets in source, prompts, docs, or logs.
5. Push to public only after checks pass.

## Recommended Commands Before Push

Run these from repository root after `git init`:

```powershell
git check-ignore -v .env .env.example .vscode/settings.json
git add .
git status
```

Search for likely secrets before commit:

```powershell
Get-ChildItem -Recurse -File | Select-String -Pattern "API_KEY|SECRET|TOKEN|PASSWORD|PRIVATE KEY|BEGIN RSA" -SimpleMatch
```

If `.env` was accidentally staged/tracked, untrack it:

```powershell
git rm --cached .env
```

## Environment Variable Usage

Runtime code reads:

- `GRANITE_ENDPOINT`
- `GRANITE_API_KEY`
- `GRANITE_MODEL` (optional)

Keep real values only in local `.env` or secure secret stores.
