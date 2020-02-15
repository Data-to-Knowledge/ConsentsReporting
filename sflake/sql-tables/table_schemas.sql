CREATE or replace TABLE "ConsentedAllocation" (
	"RecordNumber" TEXT(100),
	"HydroGroup" TEXT(100),
	"AllocationBlock" TEXT(100),
	"Wap" TEXT(100),
    "GwSpatialUnitId" TEXT(100),
    "SwSpatialUnitId" TEXT(100),
    "SpatialUnitId" TEXT(100),
    "Combined" Boolean,
    "ConsentStatus" TEXT(300),
    "FromDate" TIMESTAMP(0),
    "ToDate" TIMESTAMP(0),
  	"FromMonth" INTEGER,
	"ToMonth" INTEGER,
	"AllocatedRate" INTEGER,
	"AllocatedAnnualVolume" INTEGER,
    "EffectiveFromDate" TIMESTAMP(0),
  CONSTRAINT pkCA PRIMARY KEY ("RecordNumber", "HydroGroup", "AllocationBlock", "Wap")
)

create or replace TABLE "Waps" (
	"Wap" VARCHAR(20),
	"SD1_7Day" INTEGER,
	"SD1_30Day" INTEGER,
	"SD1_150Day" INTEGER,
	"Storativity" BOOLEAN,
	"GwSpatialUnitId" text(100),
    "SwSpatialUnitId" text(100),
    "DistanceToSw" integer,
	"Combined" BOOLEAN,
	"NzTmX" INTEGER,
	"NzTmY" INTEGER,
    "EffectiveFromDate" TIMESTAMP(0),
  CONSTRAINT pkWap PRIMARY KEY ("Wap")
);

create or replace TABLE "GwZoneAllocation" (
	"SpatialUnitId" VARCHAR(100),
	"AllocationBlock" VARCHAR(100),
	"AllocatedVolume" NUMBER(38,0),
	"NewAllocationInProgress" NUMBER(38,0),
	"EffectiveFromDate" TIMESTAMP_NTZ(0),
	constraint PKGWZONEALLO primary key ("SpatialUnitId", "AllocationBlock")
);

CREATE or replace TABLE "SwZoneAllocation" (
	"SpatialUnitId" TEXT(100),
	"AllocationBlock" TEXT(100),
    "Month" integer,
	"AllocatedRate" INTEGER,
	"NewAllocationInProgress" INTEGER,
    "EffectiveFromDate" TIMESTAMP(0),
  CONSTRAINT pkSwZoneAllo PRIMARY KEY ("SpatialUnitId", "AllocationBlock", "Month")
);

CREATE or replace TABLE "GwZoneLimits" (
	"ManagementGroupId" integer,
    "SpatialUnitId" TEXT(100),
	"AllocationBlock" TEXT(100),
    "Name" TEXT(100),
	"PlanName" text(100),
    "PlanSection" TEXT(100),
    "PlanTable" TEXT(100),
    "AllocationLimit" integer,
    "Units" TEXT(100),
    "Notes" TEXT(300),
    "EffectiveFromDate" TIMESTAMP(0),
  CONSTRAINT pkGwZoneAllo PRIMARY KEY ("ManagementGroupId", "AllocationBlock")
);

CREATE or replace TABLE "SwZoneLimits" (
	"ManagementGroupId" integer,
  "SpatialUnitId" TEXT(100),
	"AllocationBlock" TEXT(100),
  "Month" Integer,
  "Name" TEXT(100),
	"PlanName" text(100),
  "PlanSection" TEXT(100),
  "PlanTable" TEXT(100),
  "AllocationLimit" integer,
  "Units" TEXT(100),
  "Notes" TEXT(300),
  "EffectiveFromDate" TIMESTAMP(0),
  CONSTRAINT pkSwZoneAllo PRIMARY KEY ("ManagementGroupId", "AllocationBlock", "Month")
);
