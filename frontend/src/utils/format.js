export function formatCurrency(amount, currency = "USD") {
  const numericAmount = Number(amount ?? 0)

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(numericAmount)
}

export function formatDate(dateValue) {
  if (!dateValue) {
    return "-"
  }

  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(dateValue))
}

export function formatDateTime(dateValue) {
  if (!dateValue) {
    return "-"
  }

  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(dateValue))
}
