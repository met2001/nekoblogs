let warn_message = document.querySelector("#warning");
let button = document.querySelector("#submit");

let username_input = document.querySelector("#username");
let password_input = document.querySelector("#password");

button.addEventListener("click", (event) => {
    // Prevent the default form submission behavior to avoid page refresh
    

    if (username_input.value != "" && password_input.value != "") {
        let data = {
            username: username_input.value,
            password: password_input.value
        };

        fetch("https://neko-blogs-a52478cbe33c.herokuapp.com/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data),
            credentials: "include"  // Ensure cookies are included in the request
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("HTTP Error");
            }
            return response.json();
        })
        .then(data => {
            console.log("Success:", data);
            warn_message.textContent = data.message;
            // You can also do any DOM updates or redirect here
        })
        .catch(error => {
            console.error("Error:", error);
            warn_message.textContent = "An error occurred!";
        });
    } else {
        alert("Please fill in the username and password.");
    }
});
