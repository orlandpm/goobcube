from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def editor():
    level = {
        
    }
    return render_template('editor.html', level)

if __name__ == '__main__':
    app.run(debug=True)
