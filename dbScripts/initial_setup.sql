IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'customer_churn_db')
BEGIN
	CREATE DATABASE customer_churn_db
END

USE [customer_churn_db]


IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'customers' AND TABLE_SCHEMA = 'dbo')
BEGIN
	CREATE TABLE [dbo].[customers](
		[Id] [int] PRIMARY KEY IDENTITY(1,1),
		[CreditScore] [int] NOT NULL,
		[Age] [tinyint] NOT NULL,
		[Tenure] [float] NOT NULL,
		[Balance] [float] NOT NULL,
		[NumOfProducts] [tinyint] NOT NULL,
		[HasCrCard] [bit] NOT NULL,
		[IsActiveMember] [bit] NOT NULL,
		[EstimatedSalary] [float] NOT NULL,
		[Exited] [bit] NOT NULL,
		[Geography_Germany] [float] NOT NULL,
		[Geography_Spain] [float]  NOT NULL,
		[Gender_Male] [float] NOT NULL,  
		[CreditScoreTenureRatio] [float] NOT NULL, 
		[TenureAgeRatio] [float] NOT NULL, 
		[BalanceSEstimatedalaryRatio] [float] NOT NULL, 
		[BalanceAgeRatio] [float] NOT NULL
	)
END


