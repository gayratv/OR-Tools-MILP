CREATE DATABASE IF NOT EXISTS school_sheduller
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE school_sheduller;

create table user
(
    user_id   int auto_increment
        primary key,
    name varchar(255) null
);

create table jobs
(
    job_id  int auto_increment
        primary key,
    user_id int null,
    constraint jobs_user_id_fk
        foreign key (user_id) references user (user_id) on delete cascade
);

CREATE TABLE calculation_results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    -- Поля из solution_stats
    status VARCHAR(255),
    objective_value DOUBLE,
    wall_time_s DOUBLE,
    total_lonely_lessons INT,
    total_teacher_windows INT,
    
    -- JSON-представления остальных данных
    weights_json JSON,
    input_data_json JSON,
    solution_maps_json JSON,
    display_maps_json JSON,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE schedule_details (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    class_name VARCHAR(255) NOT NULL,
    subject_name VARCHAR(255) NOT NULL,
    teacher_name VARCHAR(255) NOT NULL,
    day VARCHAR(50) NOT NULL,
    period INT NOT NULL,
    subgroup_id INT NULL, -- Может быть NULL для неподгрупповых занятий
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

