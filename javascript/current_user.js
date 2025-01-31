let logged = document.querySelector("#logged-in");
let login_status = "https://neko-blogs-a52478cbe33c.herokuapp.com/";

// Function to check login status
let login_stats = () => {
    fetch(login_status, {
        method: "GET",
        credentials: "include",  // Ensures session cookie is sent
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Error fetching session status");
        }
        return response.json();
    })
    .then(data => {
        console.log("Success", data);
        if (data.user) {
            logged.textContent = `Logged in as: ${data.user}`;
        } else {
            logged.textContent = "Not logged in";
        }
    })
    .catch(error => {
        console.error("Error:", error);
        logged.textContent = "Failed to check session.";
    });
};

// Only call the function once when the page loads
window.addEventListener("load", login_stats);
