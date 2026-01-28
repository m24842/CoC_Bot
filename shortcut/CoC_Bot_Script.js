// --- CONFIGS ---
let action = args.shortcutParameter.action.toLowerCase() // "pause" or "resume"
let base_url = args.shortcutParameter.url
let auth = args.shortcutParameter.auth // "username:password"
let instance_ids = args.shortcutParameter.ids // ex. "main", "alt", etc.

// --- AUTH HEADER ---
let authHeader = `Basic ${Data.fromString(auth).toBase64String()}`

// --- POST REQUESTS ---
for (let id of instance_ids) {
  let fullUrl = `${base_url}/${id}/end_time`

  let req = new Request(fullUrl)
  req.method = "POST"

  req.headers = {
    "Authorization": authHeader,
    "Content-Type": "application/json"
  }

  req.body = JSON.stringify({
    time: Number(action==="pause")
  })

  try {
    req.load()
  } catch (err) {
    continue
  }
}

Script.complete()