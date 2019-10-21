-- Drop table

-- DROP TABLE ConsentsReporting.Accela.vAct_Water_AssociatedPermits GO

CREATE TABLE ConsentsReporting.Accela.vAct_Water_AssociatedPermits (
	RecordNumber varchar(20) COLLATE Latin1_General_CI_AS NOT NULL,
	OtherRecordNumber varchar(20) COLLATE Latin1_General_CI_AS NOT NULL,
	Relationship varchar(100) COLLATE Latin1_General_CI_AS NULL,
	CombinedAnnualVolume float NULL,
	LinkedStatus varchar(100) COLLATE Latin1_General_CI_AS NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	CONSTRAINT pklinked1 PRIMARY KEY (RecordNumber,OtherRecordNumber)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.Accela.vAct_Water_Divertwater_Water GO

CREATE TABLE ConsentsReporting.Accela.vAct_Water_Divertwater_Water (
	RecordNumber varchar(20) COLLATE Latin1_General_CI_AS NOT NULL,
	DivertType varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	WAP varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	LowFlowCondition varchar(100) COLLATE Latin1_General_CI_AS NULL,
	ConsentedRate float NULL,
	ConsentedMultiDayVolume float NULL,
	ConsentedMultiDayPeriod float NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	CONSTRAINT pkdivert1 PRIMARY KEY (RecordNumber,DivertType,WAP)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.Accela.vAct_Water_TakeWaterPermitAuthorisation GO

CREATE TABLE ConsentsReporting.Accela.vAct_Water_TakeWaterPermitAuthorisation (
	RecordNumber varchar(20) COLLATE Latin1_General_CI_AS NOT NULL,
	take_type varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	ConsentedAnnualVolume float NULL,
	LowFlowCondition varchar(100) COLLATE Latin1_General_CI_AS NULL,
	ConsentedRate float NULL,
	ConsentedMultiDayVolume float NULL,
	ConsentedMultiDayPeriod float NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	CONSTRAINT pkallovol1 PRIMARY KEY (RecordNumber,take_type)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.Accela.vAct_Water_TakeWaterPermitUse GO

CREATE TABLE ConsentsReporting.Accela.vAct_Water_TakeWaterPermitUse (
	RecordNumber varchar(20) COLLATE Latin1_General_CI_AS NOT NULL,
	UseType varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	WaterUse varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	IrrigationOf varchar(100) COLLATE Latin1_General_CI_AS NULL,
	PrimaryIrrigationType varchar(100) COLLATE Latin1_General_CI_AS NULL,
	IrrigationArea float NULL,
	ConsentedRate float NULL,
	ConsentedMultiDayVolume float NULL,
	ConsentedMultiDayPeriod float NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	CONSTRAINT pkuseallo1 PRIMARY KEY (RecordNumber,UseType,WaterUse)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.Accela.vAct_Water_TakeWaterPermitVolume GO

CREATE TABLE ConsentsReporting.Accela.vAct_Water_TakeWaterPermitVolume (
	RecordNumber varchar(20) COLLATE Latin1_General_CI_AS NOT NULL,
	take_type varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	allo_block varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	AllocatedAnnualVolume float NULL,
	FullAnnualVolume float NULL,
	IncludeInAllocation varchar(10) COLLATE Latin1_General_CI_AS NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	CONSTRAINT pktakeallo1 PRIMARY KEY (RecordNumber,take_type,allo_block)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.Accela.vAct_Water_TakeWaterWAPAllocation GO

CREATE TABLE ConsentsReporting.Accela.vAct_Water_TakeWaterWAPAllocation (
	RecordNumber varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	take_type varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	sw_allo_block varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	WAP varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	AllocatedRate float NULL,
	FromMonth varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	ToMonth varchar(100) COLLATE Latin1_General_CI_AS NULL,
	SD1 float NULL,
	SD2 float NULL,
	IncludeInSwAllocation varchar(100) COLLATE Latin1_General_CI_AS NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	CONSTRAINT pkwapallo1 PRIMARY KEY (RecordNumber,take_type,sw_allo_block,WAP,FromMonth)
) GO;
