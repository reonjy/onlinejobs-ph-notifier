# Reliable every-15-minute polls (external cron)

GitHub free-tier `schedule` is best-effort. Use an external timer.

## Preferred: cron-job.org → GitHub workflow_dispatch

### Critical (this is why you get 422)

| Must be true | Why |
|--------------|-----|
| **Request method = POST** (not GET) | GET ignores the body → GitHub says 422 “ref wasn't supplied” |
| **Request body** filled (raw text) | Empty body → 422 |
| Body is exactly `{"ref":"main"}` | No extra quotes, no form fields |
| Header `Content-Type: application/json` | So GitHub parses JSON |

### Settings that work

**URL** (either works):

```text
https://api.github.com/repos/reonjy/onlinejobs-ph-notifier/actions/workflows/onlinejobs-notify.yml/dispatches
```

or numeric id:

```text
https://api.github.com/repos/reonjy/onlinejobs-ph-notifier/actions/workflows/318610773/dispatches
```

| Field | Value |
|-------|--------|
| Method | **POST** |
| Schedule | every 15 minutes |
| Body | `{"ref":"main"}` |

**Headers:**

```text
Accept: application/vnd.github+json
Authorization: Bearer ghp_YOUR_TOKEN
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

**Token:** classic PAT with **`repo`** scope (simplest).

**Success:** HTTP **204**

Enable **Save responses** on the job, then open the failed history item — GitHub’s JSON `message` field names the exact problem.

---

## If POST body still fails on cron-job.org: Google Apps Script (GET)

cron-job only needs to **GET** a URL; the script does the GitHub POST for you.

### 1. Create script

1. Open https://script.google.com → **New project**
2. Delete sample code; paste:

```javascript
// Set Script Properties (Project Settings → Script properties):
//   GITHUB_PAT = your ghp_... token
//   CRON_SECRET = a long random string you invent

function doGet(e) {
  var props = PropertiesService.getScriptProperties();
  var secret = props.getProperty('CRON_SECRET');
  var pat = props.getProperty('GITHUB_PAT');
  var given = (e && e.parameter && e.parameter.key) || '';

  if (!secret || given !== secret) {
    return ContentService.createTextOutput('forbidden').setMimeType(ContentService.MimeType.TEXT);
  }
  if (!pat) {
    return ContentService.createTextOutput('missing pat').setMimeType(ContentService.MimeType.TEXT);
  }

  var url =
    'https://api.github.com/repos/reonjy/onlinejobs-ph-notifier/actions/workflows/onlinejobs-notify.yml/dispatches';
  var res = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    headers: {
      Accept: 'application/vnd.github+json',
      Authorization: 'Bearer ' + pat,
      'X-GitHub-Api-Version': '2022-11-28',
    },
    payload: JSON.stringify({ ref: 'main' }),
    muteHttpExceptions: true,
  });

  return ContentService.createTextOutput(
    'github_status=' + res.getResponseCode() + ' body=' + res.getContentText()
  ).setMimeType(ContentService.MimeType.TEXT);
}
```

3. **Project Settings → Script properties** add:
   - `GITHUB_PAT` = your token  
   - `CRON_SECRET` = e.g. `oj_poll_9f3k2x` (anything long/random)

4. **Deploy → New deployment → Web app**
   - Execute as: **Me**
   - Who has access: **Anyone**
   - Deploy → copy the **Web app URL**

### 2. cron-job.org (simple GET)

| Field | Value |
|-------|--------|
| URL | `https://script.google.com/macros/s/XXXX/exec?key=oj_poll_9f3k2x` |
| Method | **GET** |
| Schedule | every 15 minutes |
| Headers / body | none needed |

Test run should show `github_status=204`.  
Then Actions should show a new workflow run.

---

## Alternative: repository_dispatch

**URL:**
```text
https://api.github.com/repos/reonjy/onlinejobs-ph-notifier/dispatches
```

**Body:**
```json
{"event_type":"poll"}
```

Fine-grained PAT needs **Contents: Read and write** for this endpoint.

---

## Security

- Never commit the PAT
- Prefer classic `repo` scope limited by you rotating it
- For Apps Script, use a strong `CRON_SECRET` in the query string
