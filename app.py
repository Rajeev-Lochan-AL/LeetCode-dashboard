from flask import Flask, render_template, jsonify
import pandas as pd

app = Flask(__name__, static_folder='styles', static_url_path='/styles')

DATA_FILE = 'Leetcode Status.xlsx'

def get_processed_data():
    df = pd.read_excel(DATA_FILE)
    
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
    df = get_processed_data()
    
    total_students = len(df)
    active_students = int((df['Total Completed'] > 0).sum())
    not_attended_count = total_students - active_students
    
    # Sort all students by total solved descending
    sorted_df = df.sort_values(by=['Total Completed', 'Hard', 'Med.', 'Easy'], ascending=False)
    
    # Active students vs Not attended
    active_df = sorted_df[sorted_df['Total Completed'] > 0].copy()
    not_attended_df = sorted_df[sorted_df['Total Completed'] == 0].copy()
    
    # Top 10 Performers
    top_10 = active_df.head(10).to_dict(orient='records')
    
    return jsonify({
        'summary': {
            'total_students': total_students,
            'active_students': active_students,
            'not_attended_count': not_attended_count
        },
        'top_10': top_10,
        'active_students_list': active_df.to_dict(orient='records'),
        'not_attended_list': not_attended_df.to_dict(orient='records')
    })

if __name__ == '__main__':
    app.run(debug=True)