const API_BASE = "/api"

function formatErrorDetail(detail) {
  if (typeof detail === "string") {
    return detail
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") {
          return item
        }

        if (item?.msg) {
          return item.msg
        }

        return JSON.stringify(item)
      })
      .join(", ")
  }

  if (detail && typeof detail === "object") {
    return detail.message || JSON.stringify(detail)
  }

  return "Request failed"
}

export async function request(path, options = {}) {
  const headers = options.body
    ? {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      }
    : options.headers || {}

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  const contentType = response.headers.get("content-type") || ""
  const isJson = contentType.includes("application/json")

  let data = null

  if (response.status !== 204) {
    data = isJson ? await response.json() : await response.text()
  }

  if (!response.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? data.detail
        : data

    throw new Error(formatErrorDetail(detail))
  }

  return data
}
