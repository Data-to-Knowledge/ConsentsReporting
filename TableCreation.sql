-- Drop table

-- DROP TABLE ConsentsReporting.dbo.Activity GO

CREATE TABLE ConsentsReporting.dbo.Activity (
	ActivityID int IDENTITY(1,1) NOT NULL,
	ActivityType varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	HydroFeatureID int NOT NULL,
	Description varchar(299) COLLATE Latin1_General_CI_AS NULL,
	ModifiedDate datetime DEFAULT getdate() NOT NULL,
	CONSTRAINT Activity_UN UNIQUE (ActivityType,HydroFeatureID),
	CONSTRAINT pkActivity PRIMARY KEY (ActivityID),
	CONSTRAINT fk_Activity_HydroFeature FOREIGN KEY (HydroFeatureID) REFERENCES ConsentsReporting.dbo.HydroFeature(HydroFeatureID)
) GO
CREATE UNIQUE INDEX Activity_UN ON ConsentsReporting.dbo.Activity (ActivityType,HydroFeatureID) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.AlloBlock GO

CREATE TABLE ConsentsReporting.dbo.AlloBlock (
	AlloBlockID int IDENTITY(1,1) NOT NULL,
	AllocationBlock varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	HydroFeatureID int NOT NULL,
	Description varchar(299) COLLATE Latin1_General_CI_AS NULL,
	ModifiedDate datetime DEFAULT getdate() NOT NULL,
	CONSTRAINT AlloBlock_UN UNIQUE (AllocationBlock,HydroFeatureID),
	CONSTRAINT pkAlloBlock PRIMARY KEY (AlloBlockID),
	CONSTRAINT fk_AlloBlock_HydroFeature FOREIGN KEY (HydroFeatureID) REFERENCES ConsentsReporting.dbo.HydroFeature(HydroFeatureID)
) GO
CREATE UNIQUE INDEX AlloBlock_UN ON ConsentsReporting.dbo.AlloBlock (AllocationBlock,HydroFeatureID) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.AllocatedRateVolume GO

CREATE TABLE ConsentsReporting.dbo.AllocatedRateVolume (
	CrcAlloSiteID int NOT NULL,
	AllocatedRate numeric(9,2) NOT NULL,
	AllocatedAnnualVolume bigint NOT NULL,
	FromMonth int NOT NULL,
	ToMonth int NOT NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	CONSTRAINT pkAllocatedRateVolume PRIMARY KEY (CrcAlloSiteID),
	CONSTRAINT AllocatedRateVolume_CrcAlloSite_FK FOREIGN KEY (CrcAlloSiteID) REFERENCES ConsentsReporting.dbo.CrcAlloSite(CrcAlloSiteID)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.[Attributes] GO

CREATE TABLE ConsentsReporting.dbo.[Attributes] (
	AttributeID int IDENTITY(1,1) NOT NULL,
	[Attribute] varchar(50) COLLATE Latin1_General_CI_AS NOT NULL,
	Description varchar(299) COLLATE Latin1_General_CI_AS NULL,
	ModifiedDate datetime DEFAULT getdate() NOT NULL,
	CONSTRAINT pkAttributes PRIMARY KEY (AttributeID)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.ConsentedAttributes GO

CREATE TABLE ConsentsReporting.dbo.ConsentedAttributes (
	CrcActSiteID int NOT NULL,
	AttributeID int NOT NULL,
	Value varchar(299) COLLATE Latin1_General_CI_AS NOT NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	CONSTRAINT ConsentedAttributes_PK PRIMARY KEY (CrcActSiteID,AttributeID),
	CONSTRAINT ConsentedAttributes_Attributes_FK FOREIGN KEY (AttributeID) REFERENCES ConsentsReporting.dbo.[Attributes](AttributeID),
	CONSTRAINT ConsentedAttributes_CrcActSite_FK FOREIGN KEY (CrcActSiteID) REFERENCES ConsentsReporting.dbo.CrcActSite(CrcActSiteID)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.ConsentedRateVolume GO

CREATE TABLE ConsentsReporting.dbo.ConsentedRateVolume (
	CrcActSiteID int NOT NULL,
	ConsentedRate numeric(9,2) NULL,
	ConsentedMultiDayVolume int NULL,
	ConsentedMultiDayPeriod int NULL,
	ConsentedAnnualVolume bigint NULL,
	FromMonth int NOT NULL,
	ToMonth int NOT NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	CONSTRAINT pkConsentedRateVolume PRIMARY KEY (CrcActSiteID),
	CONSTRAINT ConsentedRateVolume_CrcActSite_FK_1 FOREIGN KEY (CrcActSiteID) REFERENCES ConsentsReporting.dbo.CrcActSite(CrcActSiteID)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.ConsentsSites GO

CREATE TABLE ConsentsReporting.dbo.ConsentsSites (
	SiteID int IDENTITY(1,1) NOT NULL,
	ExtSiteID varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	ModifiedDate datetime DEFAULT getdate() NOT NULL,
	SiteName varchar(299) COLLATE Latin1_General_CI_AS NULL,
	Geo geometry NULL,
	CONSTRAINT ConsentsSites_UN UNIQUE (ExtSiteID),
	CONSTRAINT pkConsentsSites PRIMARY KEY (SiteID)
) GO
CREATE UNIQUE INDEX ConsentsSites_UN ON ConsentsReporting.dbo.ConsentsSites (ExtSiteID) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.CrcActSite GO

CREATE TABLE ConsentsReporting.dbo.CrcActSite (
	CrcActSiteID int IDENTITY(1,1) NOT NULL,
	RecordNumber varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	ActivityID int NOT NULL,
	SiteID int NOT NULL,
	SiteActivity bit NOT NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	SiteType varchar(29) COLLATE Latin1_General_CI_AS NULL,
	CONSTRAINT pkConsentedRateVolume_dup PRIMARY KEY (CrcActSiteID),
	CONSTRAINT fk_ConsentedRateVolume_Activity1 FOREIGN KEY (ActivityID) REFERENCES ConsentsReporting.dbo.Activity(ActivityID),
	CONSTRAINT fk_ConsentedRateVolume_ConsentsSites1 FOREIGN KEY (SiteID) REFERENCES ConsentsReporting.dbo.ConsentsSites(SiteID),
	CONSTRAINT fk_ConsentedRateVolume_Permit1 FOREIGN KEY (RecordNumber) REFERENCES ConsentsReporting.dbo.Permit(RecordNumber)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.CrcAlloSite GO

CREATE TABLE ConsentsReporting.dbo.CrcAlloSite (
	CrcAlloSiteID int IDENTITY(1,1) NOT NULL,
	RecordNumber varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	AlloBlockID int NOT NULL,
	SiteID int NOT NULL,
	SiteAllo bit NOT NULL,
	SiteType varchar(29) COLLATE Latin1_General_CI_AS NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	CONSTRAINT CrcAlloSite_UN UNIQUE (RecordNumber,AlloBlockID,SiteID),
	CONSTRAINT pkCrcAlloSite PRIMARY KEY (CrcAlloSiteID),
	CONSTRAINT CrcAlloSite_AlloBlock_FK FOREIGN KEY (AlloBlockID) REFERENCES ConsentsReporting.dbo.AlloBlock(AlloBlockID),
	CONSTRAINT CrcAlloSite_ConsentsSites_FK FOREIGN KEY (SiteID) REFERENCES ConsentsReporting.dbo.ConsentsSites(SiteID),
	CONSTRAINT CrcAlloSite_Permit_FK FOREIGN KEY (RecordNumber) REFERENCES ConsentsReporting.dbo.Permit(RecordNumber)
) GO
CREATE UNIQUE INDEX CrcAlloSite_UN ON ConsentsReporting.dbo.CrcAlloSite (RecordNumber,AlloBlockID,SiteID) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.HydroFeature GO

CREATE TABLE ConsentsReporting.dbo.HydroFeature (
	HydroFeatureID int IDENTITY(1,1) NOT NULL,
	HydroFeature varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	ModifiedDate datetime DEFAULT getdate() NOT NULL,
	CONSTRAINT pkHydroFeature PRIMARY KEY (HydroFeatureID)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.LinkedPermits GO

CREATE TABLE ConsentsReporting.dbo.LinkedPermits (
	CrcActSiteID int NOT NULL,
	OtherCrcActSiteID int NOT NULL,
	Relationship varchar(29) COLLATE Latin1_General_CI_AS NOT NULL,
	LinkedStatus varchar(59) COLLATE Latin1_General_CI_AS NULL,
	CombinedRate numeric(9,2) NULL,
	CombinedMultiDayVolume int NULL,
	CombinedMultiDayPeriod int NULL,
	CombinedAnnualVolume bigint NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	CONSTRAINT LinkedPermits_PK PRIMARY KEY (CrcActSiteID,OtherCrcActSiteID),
	CONSTRAINT LinkedPermits_CrcActSite_FK FOREIGN KEY (CrcActSiteID) REFERENCES ConsentsReporting.dbo.CrcActSite(CrcActSiteID),
	CONSTRAINT LinkedPermits_CrcActSite_FK_1 FOREIGN KEY (OtherCrcActSiteID) REFERENCES ConsentsReporting.dbo.CrcActSite(CrcActSiteID)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.Log GO

CREATE TABLE ConsentsReporting.dbo.Log (
	RunTimeStart datetime2(2) NOT NULL,
	RunTimeEnd datetime2(2) NOT NULL,
	DataFromTime datetime2(2) NOT NULL,
	InternalTable varchar(79) COLLATE Latin1_General_CI_AS NOT NULL,
	RunResult varchar(9) COLLATE Latin1_General_CI_AS NOT NULL,
	Comment varchar(299) COLLATE Latin1_General_CI_AS NULL
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.LowFlowConditions GO

CREATE TABLE ConsentsReporting.dbo.LowFlowConditions (
	CrcAlloSiteID int NOT NULL,
	BandNumber int NOT NULL,
	BandName varchar(100) COLLATE Latin1_General_CI_AS NULL,
	MinTrigger float NOT NULL,
	MaxTrigger float NOT NULL,
	MinAllocation int NOT NULL,
	MaxAllocation int NOT NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	CONSTRAINT LowFlowConditions_PK PRIMARY KEY (CrcAlloSiteID),
	CONSTRAINT LowFlowConditions_CrcAlloSite_FK FOREIGN KEY (CrcAlloSiteID) REFERENCES ConsentsReporting.dbo.CrcAlloSite(CrcAlloSiteID)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.LowFlowSite GO

CREATE TABLE ConsentsReporting.dbo.LowFlowSite (
	SiteID int NOT NULL,
	NZTMX int NOT NULL,
	NZTMY int NOT NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	CONSTRAINT LowFlowSite_PK PRIMARY KEY (SiteID),
	CONSTRAINT LowFlowSite_ConsentsSites_FK FOREIGN KEY (SiteID) REFERENCES ConsentsReporting.dbo.ConsentsSites(SiteID)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.ParentChild GO

CREATE TABLE ConsentsReporting.dbo.ParentChild (
	ParentRecordNumber varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	ChildRecordNumber varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	ModifiedDate datetime DEFAULT getdate() NOT NULL,
	ParentCategory varchar(40) COLLATE Latin1_General_CI_AS NULL,
	ChildCategory varchar(40) COLLATE Latin1_General_CI_AS NULL,
	CONSTRAINT pkParentChild PRIMARY KEY (ParentRecordNumber,ChildRecordNumber),
	CONSTRAINT fk_ParentChild_Permit1 FOREIGN KEY (ParentRecordNumber) REFERENCES ConsentsReporting.dbo.Permit(RecordNumber),
	CONSTRAINT fk_ParentChild_Permit2 FOREIGN KEY (ChildRecordNumber) REFERENCES ConsentsReporting.dbo.Permit(RecordNumber)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.Permit GO

CREATE TABLE ConsentsReporting.dbo.Permit (
	RecordNumber varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	ConsentStatus varchar(29) COLLATE Latin1_General_CI_AS NOT NULL,
	FromDate date NOT NULL,
	ToDate date NOT NULL,
	NZTMX int NOT NULL,
	NZTMY int NOT NULL,
	EcanID varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	ModifiedDate datetime DEFAULT getdate() NOT NULL,
	CONSTRAINT pkPermit PRIMARY KEY (RecordNumber)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.SiteStreamDepletion GO

CREATE TABLE ConsentsReporting.dbo.SiteStreamDepletion (
	SiteID int NOT NULL,
	NZTMX int NOT NULL,
	NZTMY int NOT NULL,
	SD1_NZTMX int NULL,
	SD1_NZTMY int NULL,
	SD1_7day int NULL,
	SD1_30day int NULL,
	SD1_150day int NULL,
	SD2_NZTMX int NULL,
	SD2_NZTMY int NULL,
	SD2_7day int NULL,
	SD2_30day int NULL,
	SD2_150day int NULL,
	ModifiedDate datetime DEFAULT getdate() NOT NULL,
	CONSTRAINT pkWAP PRIMARY KEY (SiteID),
	CONSTRAINT fk_WAP_ConsentsSites FOREIGN KEY (SiteID) REFERENCES ConsentsReporting.dbo.ConsentsSites(SiteID)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.TSLowFlowRestr GO

CREATE TABLE ConsentsReporting.dbo.TSLowFlowRestr (
	CrcAlloSiteID int NOT NULL,
	RestrDate date NOT NULL,
	Allocation int NOT NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	CONSTRAINT TSLowFlowRestr_PK PRIMARY KEY (CrcAlloSiteID,RestrDate),
	CONSTRAINT TSLowFlowRestr_LowFlowConditions_FK FOREIGN KEY (CrcAlloSiteID) REFERENCES ConsentsReporting.dbo.LowFlowConditions(CrcAlloSiteID)
) GO;

-- Drop table

-- DROP TABLE ConsentsReporting.dbo.TSLowFlowSite GO

CREATE TABLE ConsentsReporting.dbo.TSLowFlowSite (
	SiteID int NOT NULL,
	RestrDate date NOT NULL,
	Measurement float NOT NULL,
	ModifiedDate datetime2(2) DEFAULT getdate() NOT NULL,
	MeasurementDate date NOT NULL,
	MeasurementMethod varchar(29) COLLATE Latin1_General_CI_AS NOT NULL,
	AppliesFromDate date NOT NULL,
	SourceSystem varchar(19) COLLATE Latin1_General_CI_AS NOT NULL,
	SourceReadLog varchar(150) COLLATE Latin1_General_CI_AS NULL,
	OPFlag varchar(9) COLLATE Latin1_General_CI_AS NULL,
	CONSTRAINT TSLowflowSite_PK PRIMARY KEY (SiteID,RestrDate),
	CONSTRAINT TSLowFlowSite_LowFlowSite_FK FOREIGN KEY (SiteID) REFERENCES ConsentsReporting.dbo.LowFlowSite(SiteID)
) GO;
