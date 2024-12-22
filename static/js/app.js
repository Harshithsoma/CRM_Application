// Example: Add interaction using AJAX
function addInteraction(customerId, type, details, outcome) {
  const data = { customer_id: customerId, type, details, outcome };

  fetch("/add_interaction", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
    .then((response) => response.json())
    .then((data) => alert(data.message))
    .catch((error) => console.error("Error:", error));
}
