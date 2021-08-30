# syntax=docker/dockerfile:1
FROM python:3

# Install discord package
RUN pip install discord

# Make main directory and set as workspace
RUN mkdir /bot
WORKDIR /bot

# Copy files
COPY word-count-bot.py /bot
COPY create-table.sql /bot

# Make db directory as a volume mount point
VOLUME [ "/bot/db" ]

# Create user and set as current
RUN groupadd -r discord-bot && useradd --no-log-init -r -g discord-bot bot-user
USER bot-user

# Run the bot
CMD ["python", "./word-count-bot.py"]