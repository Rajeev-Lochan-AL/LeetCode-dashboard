import io
import re
from flask import Flask, render_template, jsonify, send_file
import pandas as pd
import requests

app = Flask(__name__, static_folder='styles', static_url_path='/styles')

DATA_FILE = 'Leetcode Status.xlsx'

def extract_username(profile_url):
    """Extracts username from LeetCode URL (e.g., https://leetcode.com/u/username/ -> username)."""
    if not isinstance(profile_url, str) or not profile_url.strip() or profile_url == '#':
        return None
    
    # Matches patterns like /u/username/ or /username/
    match = re.search(r'leetcode\.com/(?:u/)?([^/]+)', profile_url)
    return match.group(1) if match else None

def fetch_leetcode_stats(username):
    """Fetches problem solved metrics directly from LeetCode's public GraphQL API."""
    url = "https://leetcode.com/graphql"
    query = """
    query userSessionProgress($username: String!) {
      matchedUser(username: $username) {
        submitStats {
          acSubmissionNum {
            difficulty
            count
          }
        }
      }
    }
    """
    
    try:
        response = requests.post(
            url, 
            json={'query': query, 'variables': {'username': username}},
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            user_data = data.get('data', {}).get('matchedUser')
            if user_data:
                stats = user_data['submitStats']['acSubmissionNum']
                
                # Parse difficulty counts
                counts = {item['difficulty']: item['count'] for item in stats}
                return {
                    'Easy': counts.get('Easy', 0),
                    'Med.': counts.get('Medium', 0),
                    'Hard': counts.get('Hard', 0),
                    'Total Completed': counts.get('All', 0)
                }
    except Exception as e:
        print(f"Failed to fetch data for {username}: {e}")
        
    return None

def get_live_processed_data():
    """Reads base student list, fetches live stats, and updates numbers."""
    df = pd.read_excel(DATA_FILE)
    
    for idx, row in df.iterrows():
        username = extract_username(row.get('Leetcode Link'))
        if username:
            live_stats = fetch_leetcode_stats(username)
            if live_stats:
                df.at[idx, 'Easy'] = live_stats['Easy']
                df.at[idx, 'Med.'] = live_stats['Med.']
                df.at[idx, 'Hard'] = live_stats['Hard']
                df.at[idx, 'Total Completed'] = live_stats['Total Completed']

    # Fallback cleanup
    df['Leetcode Link'] = df['Leetcode Link'].fillna('#')
    df['Easy'] = df['Easy'].fillna(0).astype(int)
    df['Med.'] = df['Med.'].fillna(0).astype(int)
    df['Hard'] = df['Hard'].fillna(0).astype(int)
    df['Total Completed'] = df['Total Completed'].fillna(0).astype(int)
    
    return df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def api_stats():
    df = get_live_processed_data()
    
    total_students = len(df)
    active_students = int((df['Total Completed'] > 0).sum())
    not_attended_count = total_students - active_students
    
    sorted_df = df.sort_values(by=['Total Completed', 'Hard', 'Med.', 'Easy'], ascending=False)
    
    active_df = sorted_df[sorted_df['Total Completed'] > 0].copy()
    not_attended_df = sorted_df[sorted_df['Total Completed'] == 0].copy()
    
    return jsonify({
        'summary': {
            'total_students': total_students,
            'active_students': active_students,
            'not_attended_count': not_attended_count
        },
        'top_10': active_df.head(10).to_dict(orient='records'),
        'active_students_list': active_df.to_dict(orient='records'),
        'not_attended_list': not_attended_df.to_dict(orient='records')
    })

@app.route('/download')
def download_excel():
    """Fetches live data and triggers an .xlsx download with clean text formatting for reg numbers."""
    df = get_live_processed_data()
    
    # Ensure Register Number is clean string without decimals or scientific notation
    if 'REGISTER NUMBER' in df.columns:
        df['REGISTER NUMBER'] = df['REGISTER NUMBER'].astype(str).str.replace(r'\.0$', '', regex=True)
    
    output = io.BytesIO()
    
    # Use Openpyxl engine to write and format
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='LeetCode Status')
        
        # Access openpyxl worksheet to set explicit text cell formatting
        worksheet = writer.sheets['LeetCode Status']
        reg_col_idx = df.columns.get_loc('REGISTER NUMBER') + 1  # 1-based index
        
        for row in range(2, len(df) + 2):  # Skip header row
            cell = worksheet.cell(row=row, column=reg_col_idx)
            cell.number_format = '@'  # Force Excel Text Format
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='LeetCode_Status_Tracker.xlsx'
    )

if __name__ == '__main__':
    app.run(debug=True)