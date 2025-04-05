Create database fraud_detection;
show databases;

use fraud_detection;
show tables;


select * from merchants;
select * from addresses;
select * from cards;
select * from credit_data;
select * from user;
select * from transaction;


ALTER TABLE merchants ADD PRIMARY KEY (merchant_id);


ALTER TABLE transaction ADD CONSTRAINT fk_client_id FOREIGN KEY (client_id) REFERENCES user(id);
ALTER TABLE transaction ADD CONSTRAINT fk_card_id FOREIGN KEY (card_id) REFERENCES cards(id);

ALTER TABLE cards ADD CONSTRAINT fk_client_id_cards FOREIGN KEY (client_id) REFERENCES user(id);
ALTER TABLE credit_data ADD CONSTRAINT fk_card_id_credit FOREIGN KEY (id) REFERENCES cards(id);

#fraudulent transactions 
select count(*),sum(amount) from transaction
where fraud_classification = 'Fraud';

#fraud amount (card-brand)
SELECT c.card_brand, COUNT(t.id) AS fraud_cases
FROM transaction t
JOIN cards c ON t.card_id = c.id
WHERE t.fraud_classification = 'Fraud'
GROUP BY c.card_brand;

#fraud amount(MERCHANT-STATE WISE)
SELECT m.merchant_state, sum(t.amount) AS fraud_cases
FROM transaction t
JOIN merchants m ON t.merchant_id = m.merchant_id
WHERE t.fraud_classification = 'Fraud'
GROUP BY m.merchant_state
ORDER BY fraud_cases DESC
LIMIT 10;


# Fraud_amount by merchant_id
select m.merchant_id,sum(t.amount) as total from merchants m
join transaction t  on m.merchant_id = t.merchant_id 
where fraud_classification = 'Fraud'
group by m.merchant_id
order by total desc
limit 10;

#Fraud Amount(Gender-wise)
SELECT u.gender, COUNT(t.id) AS fraud_cases
FROM transaction t
JOIN user u ON t.client_id = u.id
WHERE t.fraud_classification = 'Fraud'
GROUP BY u.gender;

#Monthly_Trend
select date_format(date,'%M')as month , sum(amount) as fraud_amount from transaction
where fraud_classification = 'Fraud' and date_format(date,'%M') is not null
group by month
order by fraud_amount desc;

#fraud transactions bt AGE-GROUP
select u.AgeGroup, sum(t.amount) as fraud_amount from transaction t 
join user u on u.id = t.client_id 
where t.fraud_classification  = 'fraud'
group by u.AgeGroup
order by fraud_amount desc;

#Running Total
SELECT 
    id, 
    client_id, 
    amount, 
    fraud_classification,
    SUM(amount) OVER (PARTITION BY client_id ORDER BY date) AS running_total
FROM transaction
WHERE fraud_classification = 'Fraud';

#Use a window function to rank clients by total fraud amount
SELECT client_id, SUM(amount) AS total_fraud, RANK() OVER (ORDER BY SUM(amount) DESC) AS ranking
FROM transaction WHERE fraud_classification = 'Fraud'
GROUP BY client_id;

#Moving Average
SELECT 
    id, 
    client_id, 
    amount, 
    fraud_classification,
    AVG(amount) OVER (PARTITION BY client_id ORDER BY date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg
FROM transaction;
SELECT client_id, SUM(amount) AS total_fraud, RANK() OVER (ORDER BY SUM(amount) DESC) AS ranking
FROM transactions WHERE fraud_classification = 'Fraud'
GROUP BY client_id;

#State-wise Fraud Trend
SELECT 
    m.merchant_state, 
    COUNT(t.id) AS fraud_cases,
    RANK() OVER (ORDER BY COUNT(t.id) DESC) AS state_fraud_rank
FROM transaction t
JOIN merchants m ON t.merchant_id = m.merchant_id
WHERE t.fraud_classification = 'Fraud'
GROUP BY m.merchant_state;

# List clients whose credit score is below 600 and have made high-value transactions (> $100)
SELECT t.client_id, c.credit_score, t.amount 
FROM transaction t 
JOIN credit_data c ON t.client_id = c.id 
WHERE c.credit_score < 600 AND t.amount > 100;


#High Risk Fraudulent Users
SELECT COUNT(DISTINCT u.id) AS HighRiskFraudulentUsers
FROM user u
JOIN transaction t ON u.id = t.client_id
WHERE u.creditscorecategory = 'Bad'
AND t.errors_indicator = 1;

#Frequent Errors
SELECT errors, COUNT(*) AS fraud_error_count
FROM transaction
WHERE fraud_classification = 'Fraud'
GROUP BY errors
ORDER BY fraud_error_count DESC;

#total errors
SELECT u.id AS user_id, u.creditscorecategory, COUNT(t.errors) AS total_errors
FROM transaction t
JOIN user u ON t.client_id = u.id
WHERE t.errors IS NOT NULL
GROUP BY u.id, u.creditscorecategory
ORDER BY total_errors DESC
LIMIT 10;

#fraud (error-indicator wise)
SELECT errors_indicator, COUNT(*) AS fraud_count
FROM transaction
WHERE fraud_classification = 'Fraud'
GROUP BY errors_indicator
ORDER BY fraud_count DESC;

#Fraud Detection By Transaction Time
SELECT id, client_id, amount, DATE_FORMAT(date, '%H:%i:%s') AS transaction_time,
    CASE 
        WHEN HOUR(date) BETWEEN 0 AND 6 THEN 'Late Night'
        WHEN HOUR(date) BETWEEN 7 AND 12 THEN 'Morning'
        WHEN HOUR(date) BETWEEN 13 AND 18 THEN 'Afternoon'
        ELSE 'Evening'
    END AS time_category
FROM transaction;

#High-Risk Users
WITH FraudUsers AS (
    SELECT client_id, COUNT(id) AS fraud_count
    FROM transaction
    WHERE fraud_classification = 'Fraud'
    GROUP BY client_id
)
SELECT u.id, u.creditscorecategory, f.fraud_count
FROM FraudUsers f
JOIN user u ON f.client_id = u.id
WHERE f.fraud_count > 5
ORDER BY f.fraud_count DESC;

#Most Fraud Prone merchants
WITH FraudMerchants AS (
    SELECT merchant_id, COUNT(id) AS fraud_cases
    FROM transaction
    WHERE fraud_classification = 'Fraud'
    GROUP BY merchant_id
)
SELECT m.merchant_id, m.merchant_city, m.merchant_state, f.fraud_cases
FROM FraudMerchants f
JOIN merchants m ON f.merchant_id = m.merchant_id
WHERE f.fraud_cases > 5
ORDER BY f.fraud_cases DESC;

#client who has done most fraudulent transactions
SELECT * FROM user 
WHERE id = (
    SELECT client_id 
    FROM transaction 
    WHERE fraud_classification = 'Fraud'
    GROUP BY client_id 
    ORDER BY COUNT(id) DESC 
    LIMIT 1
);

#hourly trend
select hour(date) as hour,sum(amount),count(*) from transaction
where fraud_classification= 'fraud'
group by hour
order by hour desc;

#Card brand with most fraud transactions
SELECT card_brand FROM cards 
WHERE id = (
    SELECT card_id FROM transaction 
    WHERE fraud_classification = 'Fraud'
    GROUP BY card_id 
    ORDER BY COUNT(id) DESC 
    LIMIT 1
);

#Fraud Detection by Transaction Time View
CREATE VIEW Fraud_By_Time AS
SELECT id, client_id, amount, DATE_FORMAT(date, '%H:%i:%s') AS transaction_time,
    CASE 
        WHEN HOUR(date) BETWEEN 0 AND 6 THEN 'Late Night'
        WHEN HOUR(date) BETWEEN 7 AND 12 THEN 'Morning'
        WHEN HOUR(date) BETWEEN 13 AND 18 THEN 'Afternoon'
        ELSE 'Evening'
    END AS time_category
FROM transaction
WHERE fraud_classification = 'Fraud';

SELECT time_category, COUNT(*) AS fraud_cases FROM Fraud_By_Time GROUP BY time_category;

#ERRORS IMPACT ON FRAUD VIEW
CREATE VIEW Errors_Impact AS
SELECT errors, COUNT(id) AS fraud_cases
FROM transaction
WHERE fraud_classification = 'Fraud' AND errors IS NOT NULL
GROUP BY errors;

SELECT * FROM Errors_Impact ORDER BY fraud_cases DESC;

#Fraud Trends by Month (Stored Procedure to Get Monthly Fraud Data)
DELIMITER $$

CREATE PROCEDURE GetMonthlyFraudTrend()
BEGIN
    SELECT YEAR(date) AS fraud_year, MONTH(date) AS fraud_month, COUNT(id) AS fraud_count
    FROM transaction
    WHERE fraud_classification = 'Fraud'
    GROUP BY YEAR(date), MONTH(date)
    ORDER BY fraud_year DESC, fraud_month DESC;
END $$

DELIMITER ;

CALL GetMonthlyFraudTrend();

#Create an index to fetch query fast
ALTER TABLE transaction MODIFY fraud_classification VARCHAR(20);

CREATE INDEX idx_fraud_classification ON transaction(fraud_classification);

SELECT * FROM transaction WHERE fraud_classification = 'Fraud';



INSERT INTO transaction (id, date, client_id, card_id, amount, use_chip, merchant_id, errors, fraud_classification, year, errors_indicator, firsttransactiondate, usertype, use_chip_classification)
VALUES (
    23761855, -- Unique ID
    '11-03-2025', -- Date
    957, -- Client ID
    2227, -- Card ID
    100800.0, -- Amount (high value for fraud)
    'Swipe Transaction', -- Use Chip
    27098, -- Merchant ID
    'Insufficient Balance', -- Errors
    'Fraud', -- Fraud Classification
    2025, -- Year
    1, -- Errors Indicator
    '02-01-2015', -- First Transaction Date
    'Repeat', -- User Type
    'Non-Chip_Based' -- Use Chip Classification
);


SELECT SUM(amount) FROM transaction WHERE id <> 23761855; -- Before Inserted


commit;


