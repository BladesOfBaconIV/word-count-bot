CREATE TABLE IF NOT EXISTS word_counts (
    user_id INT NOT NULL,
    word TEXT(32) NOT NULL,
    total INT NOT NULL DEFAULT 1,
    PRIMARY KEY (user_id, word)
);