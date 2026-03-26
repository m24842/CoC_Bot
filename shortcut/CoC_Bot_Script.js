// --- CONFIGS ---
let action = args.shortcutParameter.action.toLowerCase() // "pause" or "resume"
let base_url = args.shortcutParameter.url
let instance_ids = args.shortcutParameter.ids // ex. "main", "alt", etc.

// --- POST REQUESTS ---
for (let id of instance_ids) {
  let fullUrl = `${base_url}/${id}/end_time`

  let req = new Request(fullUrl)
  req.method = "POST"

  req.headers = {
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