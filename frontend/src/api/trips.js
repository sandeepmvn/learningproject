import { request } from "./client"

export function getApiInfo() {
  return request("/")
}

export function getHealth() {
  return request("/health")
}

export function getTrips() {
  return request("/trips")
}

export function createTrip(payload) {
  return request("/trips", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function getTrip(tripId) {
  return request(`/trips/${tripId}`)
}

export function getParticipants(tripId) {
  return request(`/trips/${tripId}/participants`)
}

export function addParticipant(tripId, payload) {
  return request(`/trips/${tripId}/participants`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function getExpenses(tripId) {
  return request(`/trips/${tripId}/expenses`)
}

export function addExpense(tripId, payload) {
  return request(`/trips/${tripId}/expenses`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function getTripSummary(tripId) {
  return request(`/trips/${tripId}/summary`)
}
