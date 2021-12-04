from flask import Flask, render_template, Response, request, abort, redirect
import json

app = Flask(__name__)
app.static_folder = "./static"
app.template_folder = "./templates"

@app.route("/")
def redirectToGithub():
    return redirect("https://github.com/bertmad3400/LectioAPI")

if __name__ == "__main__":
    app.run(debug=True)
