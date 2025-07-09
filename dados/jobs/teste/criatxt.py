import uuid
import os

def create_random_txt():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    random_filename = os.path.join(script_dir, f"{uuid.uuid4()}.txt")
    with open(random_filename, 'w') as file:
        file.write("Arquivo TXT gerado automaticamente.")
    print(f"Arquivo criado: {random_filename}")

if __name__ == "__main__":
    create_random_txt()