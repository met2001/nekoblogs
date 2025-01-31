const REG_API = `https://neko-blogs-a52478cbe33c.herokuapp.com/create_user`;

let warn_message = document.querySelector("#warning");
const button = document.querySelector("#submit");

let username_input = document.querySelector("#username");
let password_input = document.querySelector("#password");
let confPass_input = document.querySelector("#confpassword");
let email_input = document.querySelector("#email");

button.addEventListener("click", (event) => {
    // Prevent the default form submission behavior
    event.preventDefault();
    if (username_input.value != "" && password_input.value != "" && email_input.value != ""){
        if (confPass_input.value === password_input.value) {
            const data = {
                username: username_input.value,
                password: password_input.value,
                email: email_input.value
            };
            fetch(REG_API, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error("HTTP Error");
                }
                // Parse the JSON response
                return response.json();
            })
            .then(data => {
                console.log("Success:", data);
                warn_message.textContent = data.message;
            })
            .catch(error => {
                console.error("Error:", error);
                warn_message.textContent = "An error occurred!";
            });
        } else {
            alert("Passwords do not match!");
        }
    }else{
        alert("You must enter a username/password/email");
    }
    
    console.log(username_input.textContent);
    console.log(password_input.textContent);
});
