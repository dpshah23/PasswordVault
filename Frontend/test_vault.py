from vault import (
    add_credential,
    get_credentials,
    search_credentials,
    delete_credential
)


# Add
credential = add_credential(
    website="github.com",
    username="test@example.com",
    password="TestPassword123!",
    notes="Test account"
)

print("Added:")
print(credential)


# Get
print("\nAll credentials:")

credentials = get_credentials()

for item in credentials:
    print(item)


# Search
print("\nSearch result:")

results = search_credentials("github")

for item in results:
    print(item)


# Delete
print("\nDeleting credential...")

success = delete_credential(
    credential["id"]
)

print("Deleted:", success)