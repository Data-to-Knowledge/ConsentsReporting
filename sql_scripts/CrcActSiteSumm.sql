-- Drop table

-- DROP TABLE ConsentsReporting.reporting.CrcAlloSiteSumm GO

CREATE TABLE ConsentsReporting.reporting.CrcActSiteSumm (
	RecordNumber varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	Activity varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	HydroGroup varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	ExtSiteID varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	FromDate date NOT NULL,
	ToDate date NOT NULL,
	FromMonth int NOT NULL,
	ToMonth int NOT NULL,
	ConsentedRate numeric(9,2) NOT NULL,
	ConsentedMultiDayVolume int,
	ConsentedMultiDayPeriod int,
	ConsentedAnnualVolume bigint,
	WaterUse varchar(39) COLLATE Latin1_General_CI_AS NOT NULL,
	IrrigationArea int NULL,
	ConsentStatus varchar(29) COLLATE Latin1_General_CI_AS NOT NULL,
	ModifiedDate datetime2(2) NOT NULL,
	CONSTRAINT CrcActSiteSumm_PK PRIMARY KEY (RecordNumber,Activity,HydroGroup,ExtSiteID)
) GO
