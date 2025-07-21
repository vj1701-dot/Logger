<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dashboard</title>
    <style>
        .media-thumbnail {
            max-width: 100px;
            max-height: 100px;
            border-radius: 6px;
            margin: 4px;
            transition: transform 0.2s ease-in-out;
        }

        .media-thumbnail:hover {
            transform: scale(1.1);
        }

        .timestamp {
            font-size: 0.8em;
            color: #666;
            margin-top: 6px;
        }

        .task-card {
            border: 1px solid #ccc;
            border-radius: 10px;
            padding: 12px;
            background-color: #f9f9f9;
            margin: 10px 0;
            box-shadow: 1px 1px 5px rgba(0,0,0,0.1);
            transition: box-shadow 0.2s ease;
        }

        .task-card:hover {
            box-shadow: 2px 2px 10px rgba(0,0,0,0.15);
        }
    </style>
</head>
<body>
    <h1>Task Dashboard</h1>
    {% for row in tasks %}
    <div class="task-card">
        <h3>{{ row['UID'] }} - {{ row['Status'] }}</h3>
        <p><strong>Message:</strong> {{ row['Message'] }}</p>
        <p><strong>Submitted By:</strong> {{ row['Submitted By'] }}</p>
        <p><strong>Updated By:</strong> {{ row['Updated By'] }}</p>
        <p><strong>Assigned To:</strong> {{ row['Assigned To'] }}</p>
        <div class="media-section">
            {% if row['Media URL'].endswith('.jpg') or row['Media URL'].endswith('.png') %}
              <a href="{{ row['Media URL'] }}" target="_blank">
                <img src="{{ row['Media URL'] }}" class="media-thumbnail" alt="media">
              </a>
            {% endif %}
            {% if row['Media URL'].endswith('.mp4') %}
              <video class="media-thumbnail" controls>
                <source src="{{ row['Media URL'] }}" type="video/mp4">
                Your browser does not support the video tag.
              </video>
            {% endif %}
        </div>
        <div class="timestamp">{{ row['Timestamp'] | safe }}</div>
    </div>
    {% endfor %}
</body>
</html>
