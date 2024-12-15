import pickle
import streamlit_authenticator as stauth
from pathlib import Path

# User details
names = ["Prateek Agarwal", "Anubhav"]
usernames = ["Prateek", "Anubhav"]
passwords = ["abc123", "def456"]  # Plain text passwords

# Step 1: Generate hashed passwords for each user
hashed_passwords = stauth.Hasher(passwords).generate()

# Debugging print to check the structure of hashed_passwords
print("Hashed passwords:", hashed_passwords)

# Ensure hashed_passwords is a list with at least two elements
if len(hashed_passwords) < 2:
    raise ValueError("Expected at least 2 hashed passwords, but got fewer.")

# Step 2: Create a dictionary to store each user's credentials
credentials = {
    "usernames": {
        usernames[0]: {
            "name": names[0],
            "password": hashed_passwords[0],  # Directly access the hashed password
            "email": f"{usernames[0].lower()}@example.com"
        },
        usernames[1]: {
            "name": names[1],
            "password": hashed_passwords[1],  # Directly access the hashed password
            "email": f"{usernames[1].lower()}@example.com"
        }
    }
}

# Step 3: Define the path for the hashed_pw.pkl file
file_path = Path(__file__).parent / "hashed_pw.pkl"  # Use .parent to get the current directory

# Ensure that the directory exists
file_path.parent.mkdir(parents=True, exist_ok=True)

# Step 4: Write the credentials dictionary directly to the pickle file (without converting to JSON)
with file_path.open("wb") as file:
    pickle.dump(credentials, file)

print(f"Hashed passwords and user details saved to '{file_path}'.")