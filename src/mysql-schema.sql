CREATE DATABASE football_stats;

USE football_stats;

CREATE TABLE players (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    team_id INT,
    position VARCHAR(50),
    appearances INT,
    goals INT,
    assists INT
);

CREATE TABLE teams (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    city VARCHAR(100)
);

CREATE TABLE matches (
    id INT PRIMARY KEY AUTO_INCREMENT,
    team1_id INT,
    team2_id INT,
    score_team1 INT DEFAULT 0,
    score_team2 INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'not_started'
);
