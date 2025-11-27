# Codefest - Balik Penang (Track Embedded LLM)
## Installation & Setup

### 1. Import JamAI Project Tables

To run this project, you need to import the JamAI project tables:

1. **Download the project tables**  
   Download the file [`jamaibase_project_tables.parquet`](/jamaibase_project_tables.parquet) from the repository.

2. **Import the tables into JamAI**  
   - Log in to your [JamAI](https://www.jamaibase.com/) account.
   - Navigate to your project dashboard.
   - Go to **Project → Import Project**.
   - Upload the `jamaibase_project_tables.parquet` file.
   
### 2. Clone the repo
```
git clone https://github.com/LOWGUANHOONG/codefest-balikPenang.git
cd codefest-balikPenang
```

### 3. Create & activate a virtual environment
#### MacOS / Linus
```
python3 -m venv venv
source venv/bin/activate
```
#### Windows (PowerShell)
```
python -m venv venv
venv\Scripts\Activate.ps1
```

### 4. Install dependencies
``` 
pip install -r requirements.txt 
```

### 5. Update your API key and Project ID

#### In `.streamlit/secrets.toml` and `config.py` :
```
API_KEY = "YOUR_API_KEY"        # Replace with your own JamAI Base PAT
PROJECT_ID = "YOUR_PROJECT_ID"  # Replace with your actual Project ID
```

### 6. Run the application
Make sure you are in the app directory before running the command.
```
cd app
streamlit run "Labour Law QnA"
```
