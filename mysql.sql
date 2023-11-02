-- Create the Teacher table
CREATE TABLE teacher (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    teacher_branch VARCHAR(255),
    designation VARCHAR(255),
    gender VARCHAR(10)
);

-- Create the Class table
CREATE TABLE class (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id VARCHAR(10) NOT NULL,
    class_name VARCHAR(255) NOT NULL,
    day_of_week INT NOT NULL,
    class_time TIME NOT NULL,
    year INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (teacher_id) REFERENCES teacher(teacher_id)
);

-- Create the ClassNotification table
CREATE TABLE class_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id VARCHAR(10) NOT NULL,
    class_id INT NOT NULL,
    date DATE NOT NULL,
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_datetime DATETIME,
    FOREIGN KEY (class_id) REFERENCES class(id)
);

-- Create the User table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    role VARCHAR(10) NOT NULL
);

-- Create the LeaveRequest table
CREATE TABLE leave_request (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id VARCHAR(10) NOT NULL,
    class_id INT NOT NULL,
    leave_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending',
    assigned_teacher_id VARCHAR(10),
    branch_name VARCHAR(255),
    FOREIGN KEY (teacher_id) REFERENCES teacher(teacher_id)
);
