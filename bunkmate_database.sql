create database bunkmates;

use bunkmates;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(15) UNIQUE,
    name VARCHAR(50),
    password VARCHAR(255),
    roommates INT,
    joined_date DATE
);



ALTER TABLE roommates ADD COLUMN left_date DATE;

UPDATE users 
SET password='$2b$12$CZNmzRVR/PrY0sg6HLm.l.SSM06acUQ6Znmsvb/amZHkCQO2KHk3y' 
WHERE phone='8147181297';

select * from users;

insert into users(phone,name,password,roommates,joined_date) values("8147181297","jaggu","jaggu",1,'2026-03-30');


CREATE TABLE roommates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) primary key,
    role VARCHAR(50),
    joined_date VARCHAR(20)
);

ALTER TABLE roommates ADD CONSTRAINT unique_name UNIQUE (name);