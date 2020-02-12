CREATE TABLE "GwZoneAllocation" (
	"SpatialUnitId" TEXT(100),
	"AllocationBlock" TEXT(100),
  "ConsentStatus" TEXT(300),
	"AllocatedRate" INTEGER,
	"AllocatedAnnualVolume" INTEGER,
  "EffectiveFromDate" TIMESTAMP(0),
  CONSTRAINT pkGwZoneAllo PRIMARY KEY ("SpatialUnitId", "AllocationBlock", "ConsentStatus")
)

CREATE TABLE "SwZoneAllocation" (
	"SpatialUnitId" TEXT(100),
	"AllocationBlock" TEXT(100),
  "Month" integer,
  "ConsentStatus" TEXT(300),
	"AllocatedRate" INTEGER,
	"AllocatedAnnualVolume" INTEGER, 
  "EffectiveFromDate" TIMESTAMP(0),
  CONSTRAINT pkSwZoneAllo PRIMARY KEY ("SpatialUnitId", "AllocationBlock", "Month", "ConsentStatus")
)
