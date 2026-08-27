"""Express Estimate wizard payload — Pydantic mirror of frontend Zod (deep-partial, extra forbidden).

Wire JSON uses camelCase aliases; Python attrs are snake_case. Root requires ``project_details``
with non-empty ``insured_name`` and ``claim_number``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EE = ConfigDict(populate_by_name=True, extra="forbid")


class CircuitRow(BaseModel):
    model_config = _EE
    id: float | None = Field(default=None, alias="id")
    type: str | None = Field(default=None, alias="type")
    qty: str | None = Field(default=None, alias="qty")


class WindowItem(BaseModel):
    model_config = _EE
    id: float | None = Field(default=None, alias="id")
    type: str | None = Field(default=None, alias="type")
    material: str | None = Field(default=None, alias="material")
    size: str | None = Field(default=None, alias="size")
    grade: str | None = Field(default=None, alias="grade")
    quantity: str | None = Field(default=None, alias="quantity")
    finish: str | None = Field(default=None, alias="finish")
    blinds: str | None = Field(default=None, alias="blinds")
    casing_trim: str | None = Field(default=None, alias="casingTrim")
    marble_sill_replace: bool | None = Field(default=None, alias="marbleSillReplace")
    marble_sill_detach: bool | None = Field(default=None, alias="marbleSillDetach")


class DoorItem(BaseModel):
    model_config = _EE
    id: float | None = Field(default=None, alias="id")
    category: Literal["interior", "exterior", "cased-opening"] | None = Field(
        default=None, alias="category"
    )
    type: str | None = Field(default=None, alias="type")
    size: str | None = Field(default=None, alias="size")
    grade: str | None = Field(default=None, alias="grade")
    finish: str | None = Field(default=None, alias="finish")
    handle_action: str | None = Field(default=None, alias="handleAction")
    misc: str | None = Field(default=None, alias="misc")
    peep_hole: bool | None = Field(default=None, alias="peepHole")
    mail_slot: bool | None = Field(default=None, alias="mailSlot")
    non_cased: bool | None = Field(default=None, alias="nonCased")
    cased_opening: bool | None = Field(default=None, alias="casedOpening")
    casing_opening_size: str | None = Field(default=None, alias="casingOpeningSize")
    casing_finish: str | None = Field(default=None, alias="casingFinish")
    sidelites: bool | None = Field(default=None, alias="sidelites")
    sidelites_qty: str | None = Field(default=None, alias="sidelitesQty")
    sidelites_size: str | None = Field(default=None, alias="sidelitesSize")
    sidelites_grade: str | None = Field(default=None, alias="sidelitesGrade")
    panel_size: str | None = Field(default=None, alias="panelSize")
    panel_grade: str | None = Field(default=None, alias="panelGrade")
    stormdoor_assembly: bool | None = Field(default=None, alias="stormdoorAssembly")
    retrofit_in_stucco: bool | None = Field(default=None, alias="retrofitInStucco")
    clean_sensor: bool | None = Field(default=None, alias="cleanSensor")
    replace_sensor: bool | None = Field(default=None, alias="replaceSensor")


class FloorLayer(BaseModel):
    model_config = _EE
    id: float | None = Field(default=None, alias="id")
    type: str | None = Field(default=None, alias="type")
    grade: str | None = Field(default=None, alias="grade")
    application: str | None = Field(default=None, alias="application")
    action: str | None = Field(default=None, alias="action")
    vapor_barrier: bool | None = Field(default=None, alias="vaporBarrier")
    subfloor_replacement: bool | None = Field(default=None, alias="subfloorReplacement")


class NfipCleaningWall(BaseModel):
    model_config = _EE
    height: str | None = Field(default=None, alias="height")
    wall_type: str | None = Field(default=None, alias="wallType")
    ceiling_affected: bool | None = Field(default=None, alias="ceilingAffected")


class NfipCleaningFloor(BaseModel):
    model_config = _EE
    type: str | None = Field(default=None, alias="type")
    area_on_crawlspace: bool | None = Field(default=None, alias="areaOnCrawlspace")


class NfipCleaningOptions(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    wall: NfipCleaningWall | None = Field(default=None, alias="wall")
    floor: NfipCleaningFloor | None = Field(default=None, alias="floor")


class FlooringOptions(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    multiple_layers: bool | None = Field(default=None, alias="multipleLayers")
    layers: list[FloorLayer] | None = Field(default=None, alias="layers")
    vapor_barrier: bool | None = Field(default=None, alias="vaporBarrier")
    subfloor_replacement: bool | None = Field(default=None, alias="subfloorReplacement")
    f9_note: str | None = Field(default=None, alias="f9Note")


class TrimOptions(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    baseboard_height: str | None = Field(default=None, alias="baseboardHeight")
    material: str | None = Field(default=None, alias="material")
    detail: str | None = Field(default=None, alias="detail")
    finish: str | None = Field(default=None, alias="finish")
    cap: bool | None = Field(default=None, alias="cap")
    shoe: bool | None = Field(default=None, alias="shoe")
    shoe_finish: str | None = Field(default=None, alias="shoeFinish")
    subtract_cabinetry: bool | None = Field(default=None, alias="subtractCabinetry")
    vinyl_cove_enabled: bool | None = Field(default=None, alias="vinylCoveEnabled")
    vinyl_cove_size: str | None = Field(default=None, alias="vinylCoveSize")
    tile_base_enabled: bool | None = Field(default=None, alias="tileBaseEnabled")
    tile_base_grade: str | None = Field(default=None, alias="tileBaseGrade")


class WallCoveringOptions(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    material: str | None = Field(default=None, alias="material")
    type: str | None = Field(default=None, alias="type")
    replacement_height: str | None = Field(default=None, alias="replacementHeight")
    full_wall: bool | None = Field(default=None, alias="fullWall")
    ceiling_replacement_addon: bool | None = Field(default=None, alias="ceilingReplacementAddon")
    texture: bool | None = Field(default=None, alias="texture")
    texture_type: str | None = Field(default=None, alias="textureType")
    paneling_style: str | None = Field(default=None, alias="panelingStyle")
    paneling_finish: str | None = Field(default=None, alias="panelingFinish")
    paneling_grade: str | None = Field(default=None, alias="panelingGrade")
    chair_rail_action: str | None = Field(default=None, alias="chairRailAction")
    chair_rail_finish: str | None = Field(default=None, alias="chairRailFinish")


class ElectricalRoomOptions(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    outlets_110: float | None = Field(default=None, alias="outlets110")
    outlets_220: float | None = Field(default=None, alias="outlets220")
    gfi_outlets: float | None = Field(default=None, alias="gfiOutlets")
    light_switches: float | None = Field(default=None, alias="lightSwitches")
    ceiling_lights: float | None = Field(default=None, alias="ceilingLights")
    ceiling_fans: str | None = Field(default=None, alias="ceilingFans")
    bathroom_light_bar: str | None = Field(default=None, alias="bathroomLightBar")
    bathroom_light_bar_qty: float | None = Field(default=None, alias="bathroomLightBarQty")

    @field_validator("ceiling_fans", mode="before")
    @classmethod
    def _stringify_ceiling_fans(cls, v: object) -> object:
        if isinstance(v, bool) or v is None:
            return v
        if isinstance(v, int):
            return str(v)
        if isinstance(v, float):
            return str(int(v)) if v.is_integer() else str(v)
        return v


class VanityCountertop(BaseModel):
    model_config = _EE
    type: str | None = Field(default=None, alias="type")
    grade: str | None = Field(default=None, alias="grade")
    size: str | None = Field(default=None, alias="size")
    p_stop: str | None = Field(default=None, alias="pStop")
    sink: str | None = Field(default=None, alias="sink")
    action: str | None = Field(default=None, alias="action")
    faucet: str | None = Field(default=None, alias="faucet")
    faucet_action: str | None = Field(default=None, alias="faucetAction")


class VanityOptions(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    size: str | None = Field(default=None, alias="size")
    grade: str | None = Field(default=None, alias="grade")
    custom: bool | None = Field(default=None, alias="custom")
    detach_and_reset: bool | None = Field(default=None, alias="detachAndReset")
    countertop: VanityCountertop | None = Field(default=None, alias="countertop")
    backsplash_unattached: bool | None = Field(default=None, alias="backsplashUnattached")
    backsplash_action: str | None = Field(default=None, alias="backsplashAction")


class PedestalSinkOptions(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    action: str | None = Field(default=None, alias="action")


class ToiletOptions(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    action: str | None = Field(default=None, alias="action")
    seat_replacement: bool | None = Field(default=None, alias="seatReplacement")
    supply_line: bool | None = Field(default=None, alias="supplyLine")


class ShowerOptions(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    detach_and_reset: bool | None = Field(default=None, alias="detachAndReset")
    shower_faucet: str | None = Field(default=None, alias="showerFaucet")
    action_for_tub: str | None = Field(default=None, alias="actionForTub")
    jetted: bool | None = Field(default=None, alias="jetted")
    jetted_motor_replace: bool | None = Field(default=None, alias="jettedMotorReplace")
    surround: str | None = Field(default=None, alias="surround")
    tub_shower_faucet: str | None = Field(default=None, alias="tubShowerFaucet")
    mortar_bed_replace: bool | None = Field(default=None, alias="mortarBedReplace")
    mortar_bed_size: str | None = Field(default=None, alias="mortarBedSize")
    tile_curb: bool | None = Field(default=None, alias="tileCurb")
    tile_curb_size: str | None = Field(default=None, alias="tileCurbSize")
    walls: str | None = Field(default=None, alias="walls")
    tile_bench: bool | None = Field(default=None, alias="tileBench")
    tile_niche: bool | None = Field(default=None, alias="tileNiche")
    tile_niche_qty: str | None = Field(default=None, alias="tileNicheQty")
    towel_bar: bool | None = Field(default=None, alias="towelBar")
    tile_soap_dish: bool | None = Field(default=None, alias="tileSoapDish")
    tile_soap_dish_qty: str | None = Field(default=None, alias="tileSoapDishQty")
    grab_bar: bool | None = Field(default=None, alias="grabBar")
    grab_bar_qty: str | None = Field(default=None, alias="grabBarQty")
    tile_feature_strip: bool | None = Field(default=None, alias="tileFeatureStrip")
    glass_door: bool | None = Field(default=None, alias="glassDoor")
    glass_door_action: str | None = Field(default=None, alias="glassDoorAction")


class ToeKick(BaseModel):
    model_config = _EE
    size: str | None = Field(default=None, alias="size")
    back_splash: str | None = Field(default=None, alias="backSplash")
    grade: str | None = Field(default=None, alias="grade")
    glass: bool | None = Field(default=None, alias="glass")
    diagonal_installation: bool | None = Field(default=None, alias="diagonalInstallation")


class CabinetFullHeight(BaseModel):
    model_config = _EE
    type: str | None = Field(default=None, alias="type")
    grade: str | None = Field(default=None, alias="grade")
    size: str | None = Field(default=None, alias="size")


class CabinetOptions(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    size: str | None = Field(default=None, alias="size")
    grade: str | None = Field(default=None, alias="grade")
    detach_and_reset: bool | None = Field(default=None, alias="detachAndReset")
    toe_kick: ToeKick | None = Field(default=None, alias="toeKick")
    full_height: CabinetFullHeight | None = Field(default=None, alias="fullHeight")


class CountertopOptions(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    grade: str | None = Field(default=None, alias="grade")
    size: str | None = Field(default=None, alias="size")
    detach_and_reset: bool | None = Field(default=None, alias="detachAndReset")
    action: str | None = Field(default=None, alias="action")
    subdeck_replacement: bool | None = Field(default=None, alias="subdeckReplacement")


class PlumbingWaterSupplyLine(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    qty: str | None = Field(default=None, alias="qty")


class PlumbingReverseOsmosis(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")


class PlumbingGarbageDisposal(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")


class PlumbingOptions(BaseModel):
    model_config = _EE
    replace_faucet_sink: bool | None = Field(default=None, alias="replaceFaucetSink")
    dr_faucet_sink: bool | None = Field(default=None, alias="drFaucetSink")
    water_supply_line: PlumbingWaterSupplyLine | None = Field(default=None, alias="waterSupplyLine")
    reverse_osmosis: PlumbingReverseOsmosis | None = Field(default=None, alias="reverseOsmosis")
    garbage_disposal: PlumbingGarbageDisposal | None = Field(default=None, alias="garbageDisposal")


class ApplianceRefrigerator(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    size: str | None = Field(default=None, alias="size")
    grade: str | None = Field(default=None, alias="grade")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")


class ApplianceDishwasher(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    grade: str | None = Field(default=None, alias="grade")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")


class ApplianceRange(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    options: str | None = Field(default=None, alias="options")
    grade: str | None = Field(default=None, alias="grade")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")


class ApplianceCooktop(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    grade: str | None = Field(default=None, alias="grade")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")


class ApplianceWaterHeater(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    size: str | None = Field(default=None, alias="size")
    rating: str | None = Field(default=None, alias="rating")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")


class ApplianceWallOven(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    grade: str | None = Field(default=None, alias="grade")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")


class ApplianceAirHandlerACoil(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    detach_and_reset: bool | None = Field(default=None, alias="detachAndReset")


class ApplianceAirHandler(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    options: str | None = Field(default=None, alias="options")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")
    a_coil: ApplianceAirHandlerACoil | None = Field(default=None, alias="aCoil")


class ApplianceFurnace(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    btu: str | None = Field(default=None, alias="btu")
    high_efficiency: bool | None = Field(default=None, alias="highEfficiency")
    action: str | None = Field(default=None, alias="action")


class ApplianceBoiler(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")
    expansion_tank: bool | None = Field(default=None, alias="expansionTank")
    circulator_pump: bool | None = Field(default=None, alias="circulatorPump")


class ApplianceBaseboardHeat(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    size: str | None = Field(default=None, alias="size")
    action: str | None = Field(default=None, alias="action")


class ApplianceOptions(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    refrigerator: ApplianceRefrigerator | None = Field(default=None, alias="refrigerator")
    dishwasher: ApplianceDishwasher | None = Field(default=None, alias="dishwasher")
    range_: ApplianceRange | None = Field(default=None, alias="range")
    cooktop: ApplianceCooktop | None = Field(default=None, alias="cooktop")
    water_heater: ApplianceWaterHeater | None = Field(default=None, alias="waterHeater")
    wall_oven: ApplianceWallOven | None = Field(default=None, alias="wallOven")
    air_handler: ApplianceAirHandler | None = Field(default=None, alias="airHandler")
    boiler: ApplianceBoiler | None = Field(default=None, alias="boiler")
    furnace: ApplianceFurnace | None = Field(default=None, alias="furnace")
    baseboard_heat: ApplianceBaseboardHeat | None = Field(default=None, alias="baseboardHeat")


class Room(BaseModel):
    model_config = _EE
    id: float | None = Field(default=None, alias="id")
    name: str | None = Field(default=None, alias="name")
    type: str | None = Field(default=None, alias="type")
    sqft: str | None = Field(default=None, alias="sqft")
    nfip_cleaning: NfipCleaningOptions | None = Field(default=None, alias="nfipCleaning")
    flooring: FlooringOptions | None = Field(default=None, alias="flooring")
    trim: TrimOptions | None = Field(default=None, alias="trim")
    wall_covering: WallCoveringOptions | None = Field(default=None, alias="wallCovering")
    electrical: ElectricalRoomOptions | None = Field(default=None, alias="electrical")
    windows_enabled: bool | None = Field(default=None, alias="windowsEnabled")
    windows: list[WindowItem] | None = Field(default=None, alias="windows")
    doors_enabled: bool | None = Field(default=None, alias="doorsEnabled")
    doors: list[DoorItem] | None = Field(default=None, alias="doors")
    vanity: VanityOptions | None = Field(default=None, alias="vanity")
    pedestal_sink: PedestalSinkOptions | None = Field(default=None, alias="pedestalSink")
    toilet: ToiletOptions | None = Field(default=None, alias="toilet")
    shower: ShowerOptions | None = Field(default=None, alias="shower")
    cabinets: CabinetOptions | None = Field(default=None, alias="cabinets")
    countertop: CountertopOptions | None = Field(default=None, alias="countertop")
    plumbing: PlumbingOptions | None = Field(default=None, alias="plumbing")
    appliances: ApplianceOptions | None = Field(default=None, alias="appliances")
    notes: str | None = Field(default=None, alias="notes")


class ProjectDetails(BaseModel):
    model_config = _EE
    insured_name: str = Field(min_length=1, alias="insuredName")
    claim_number: str = Field(min_length=1, alias="claimNumber")
    street: str | None = Field(default=None, alias="street")
    city: str | None = Field(default=None, alias="city")
    zip_code: str | None = Field(default=None, alias="zipCode")
    depreciation_range: str | None = Field(default=None, alias="depreciationRange")
    # Legacy / optional fields (older clients)
    project_name: str | None = Field(default=None, alias="projectName")
    inspection_date: str | None = Field(default=None, alias="inspectionDate")
    property_address: str | None = Field(default=None, alias="propertyAddress")
    property_type: str | None = Field(default=None, alias="propertyType")
    pre_firm: bool | None = Field(default=None, alias="preFirm")
    adjuster_name: str | None = Field(default=None, alias="adjusterName")
    notes: str | None = Field(default=None, alias="notes")

    @field_validator("insured_name", "claim_number", "project_name", mode="before")
    @classmethod
    def _strip_required_strings(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v


# --- Exterior ---
class ExteriorPressureWash(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    perimeter_feet: str | None = Field(default=None, alias="perimeterFeet")
    regular_pwash: bool | None = Field(default=None, alias="regularPwash")
    clean_with_steam: bool | None = Field(default=None, alias="cleanWithSteam")


class ExteriorDumpster(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    count: str | None = Field(default=None, alias="count")
    size: str | None = Field(default=None, alias="size")


class ExteriorCondenser(BaseModel):
    model_config = _EE
    id: float | None = Field(default=None, alias="id")
    tonnage: str | None = Field(default=None, alias="tonnage")
    seer: str | None = Field(default=None, alias="seer")
    replace: bool | None = Field(default=None, alias="replace")
    service_call: bool | None = Field(default=None, alias="serviceCall")
    f9_note: str | None = Field(default=None, alias="f9Note")


class ExteriorPackageUnit(BaseModel):
    model_config = _EE
    id: float | None = Field(default=None, alias="id")
    unit_type: str | None = Field(default=None, alias="unitType")
    tonnage: str | None = Field(default=None, alias="tonnage")
    seer: str | None = Field(default=None, alias="seer")
    replace: bool | None = Field(default=None, alias="replace")
    service_call: bool | None = Field(default=None, alias="serviceCall")
    f9_note: str | None = Field(default=None, alias="f9Note")


class ExteriorMiniSplit(BaseModel):
    model_config = _EE
    id: float | None = Field(default=None, alias="id")
    zones: str | None = Field(default=None, alias="zones")
    high_efficiency: bool | None = Field(default=None, alias="highEfficiency")
    replace: bool | None = Field(default=None, alias="replace")
    service_call: bool | None = Field(default=None, alias="serviceCall")
    f9_note: str | None = Field(default=None, alias="f9Note")


class ExteriorHvac(BaseModel):
    model_config = _EE
    condenser_units: list[ExteriorCondenser] | None = Field(default=None, alias="condenserUnits")
    package_units: list[ExteriorPackageUnit] | None = Field(default=None, alias="packageUnits")
    mini_splits: list[ExteriorMiniSplit] | None = Field(default=None, alias="miniSplits")


class ExteriorBreakerPanel(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    amps: str | None = Field(default=None, alias="amps")
    arc_faults: bool | None = Field(default=None, alias="arcFaults")
    panel_replacement: bool | None = Field(default=None, alias="panelReplacement")
    circuit_replacement: bool | None = Field(default=None, alias="circuitReplacement")
    panel_type: str | None = Field(default=None, alias="panelType")
    circuits: list[CircuitRow] | None = Field(default=None, alias="circuits")


class ExteriorElectrical(BaseModel):
    model_config = _EE
    exterior_outlets: str | None = Field(default=None, alias="exteriorOutlets")
    disconnect_30_amp: str | None = Field(default=None, alias="disconnect30Amp")
    breaker_panel: ExteriorBreakerPanel | None = Field(default=None, alias="breakerPanel")
    meter_box: bool | None = Field(default=None, alias="meterBox")
    meter_box_qty: str | None = Field(default=None, alias="meterBoxQty")
    meter_box_size: str | None = Field(default=None, alias="meterBoxSize")


class ExteriorPaintEnabled(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")


class ExteriorSiding(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    perimeter_feet: str | None = Field(default=None, alias="perimeterFeet")
    square_feet_enabled: bool | None = Field(default=None, alias="squareFeetEnabled")
    square_feet: str | None = Field(default=None, alias="squareFeet")


class ExteriorSheathing(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    tongue_and_groove: bool | None = Field(default=None, alias="tongueAndGroove")
    replacement_height: str | None = Field(default=None, alias="replacementHeight")


class ExteriorHouseWrap(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    replacement_height: str | None = Field(default=None, alias="replacementHeight")


class ExteriorBackerBoard(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    replacement_height: str | None = Field(default=None, alias="replacementHeight")


class ExteriorWallInsulation(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    batt_rating: str | None = Field(default=None, alias="battRating")
    spray_foam_cell_type: str | None = Field(default=None, alias="sprayFoamCellType")
    replacement_height: str | None = Field(default=None, alias="replacementHeight")


class ExteriorFinishes(BaseModel):
    model_config = _EE
    exterior_paint: ExteriorPaintEnabled | None = Field(default=None, alias="exteriorPaint")
    siding: ExteriorSiding | None = Field(default=None, alias="siding")
    sheathing: ExteriorSheathing | None = Field(default=None, alias="sheathing")
    house_wrap: ExteriorHouseWrap | None = Field(default=None, alias="houseWrap")
    backer_board: ExteriorBackerBoard | None = Field(default=None, alias="backerBoard")
    wall_insulation: ExteriorWallInsulation | None = Field(default=None, alias="wallInsulation")


class Exterior(BaseModel):
    model_config = _EE
    pressure_wash: ExteriorPressureWash | None = Field(default=None, alias="pressureWash")
    dumpster: ExteriorDumpster | None = Field(default=None, alias="dumpster")
    hvac: ExteriorHvac | None = Field(default=None, alias="hvac")
    electrical: ExteriorElectrical | None = Field(default=None, alias="electrical")
    finishes: ExteriorFinishes | None = Field(default=None, alias="finishes")


# --- Foundation ---
MeasureType = Literal["sf", "lf"]
PiersType = Literal["", "short", "tall"]


class FoundationWindowRow(BaseModel):
    model_config = _EE
    id: float | None = Field(default=None, alias="id")
    type: str | None = Field(default=None, alias="type")
    size: str | None = Field(default=None, alias="size")
    quantity: str | None = Field(default=None, alias="quantity")
    material: str | None = Field(default=None, alias="material")


class FoundationACoil(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    detach_and_reset: bool | None = Field(default=None, alias="detachAndReset")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")


class FoundationAirHandlerRow(BaseModel):
    model_config = _EE
    id: float | None = Field(default=None, alias="id")
    type: str | None = Field(default=None, alias="type")
    tonnage: str | None = Field(default=None, alias="tonnage")
    heat_element_count: str | None = Field(default=None, alias="heatElementCount")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")
    a_coil: FoundationACoil | None = Field(default=None, alias="aCoil")


class FoundationFurnace(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    btu: str | None = Field(default=None, alias="btu")
    high_efficiency: bool | None = Field(default=None, alias="highEfficiency")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")


class FoundationCrawlspace(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    pre_firm: bool | None = Field(default=None, alias="preFirm")
    ac_controlled_space: bool | None = Field(default=None, alias="acControlledSpace")
    heavy_clean_area: bool | None = Field(default=None, alias="heavyCleanArea")
    perimeter_feet: str | None = Field(default=None, alias="perimeterFeet")
    piers_type: PiersType | None = Field(default=None, alias="piersType")
    piers_count: str | None = Field(default=None, alias="piersCount")
    clean_joist: bool | None = Field(default=None, alias="cleanJoist")
    belly_paper: bool | None = Field(default=None, alias="bellyPaper")
    floor_insulation: bool | None = Field(default=None, alias="floorInsulation")
    floor_insulation_type: str | None = Field(default=None, alias="floorInsulationType")
    muck: bool | None = Field(default=None, alias="muck")
    muck_heavy: bool | None = Field(default=None, alias="muckHeavy")
    standing_water: bool | None = Field(default=None, alias="standingWater")
    house_rewire: str | None = Field(default=None, alias="houseRewire")
    stair_cleaning: bool | None = Field(default=None, alias="stairCleaning")
    stairs_submerged: str | None = Field(default=None, alias="stairsSubmerged")
    tread_width: str | None = Field(default=None, alias="treadWidth")
    stringers_length: str | None = Field(default=None, alias="stringersLength")


class SandRemoval(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    cubic_feet: str | None = Field(default=None, alias="cubicFeet")
    length: str | None = Field(default=None, alias="length")
    width: str | None = Field(default=None, alias="width")
    depth: str | None = Field(default=None, alias="depth")


class Backfill(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    cubic_feet: str | None = Field(default=None, alias="cubicFeet")
    length: str | None = Field(default=None, alias="length")
    width: str | None = Field(default=None, alias="width")
    depth: str | None = Field(default=None, alias="depth")


class EnclosureRemoval(BaseModel):
    model_config = _EE
    sand_removal: SandRemoval | None = Field(default=None, alias="sandRemoval")
    backfill: Backfill | None = Field(default=None, alias="backfill")
    confined_space: bool | None = Field(default=None, alias="confinedSpace")


class FoundationInsulation(BaseModel):
    model_config = _EE
    belly_paper: bool | None = Field(default=None, alias="bellyPaper")
    floor_insulation: bool | None = Field(default=None, alias="floorInsulation")
    floor_insulation_type: str | None = Field(default=None, alias="floorInsulationType")
    floor_insulation_replacement_height: str | None = Field(
        default=None, alias="floorInsulationReplacementHeight"
    )
    confined_space: bool | None = Field(default=None, alias="confinedSpace")


class SubgradeDrywall(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    replacement_height: str | None = Field(default=None, alias="replacementHeight")
    measure_type: MeasureType | None = Field(default=None, alias="measureType")


class SubgradeWallInsulation(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    replacement_height: str | None = Field(default=None, alias="replacementHeight")
    measure_type: MeasureType | None = Field(default=None, alias="measureType")


class SubgradeFoundationalDoor(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    action: str | None = Field(default=None, alias="action")


class SubgradeAreaCoverage(BaseModel):
    model_config = _EE
    drywall: SubgradeDrywall | None = Field(default=None, alias="drywall")
    wall_insulation: SubgradeWallInsulation | None = Field(default=None, alias="wallInsulation")
    foundational_door: SubgradeFoundationalDoor | None = Field(default=None, alias="foundationalDoor")
    foundational_windows_enabled: bool | None = Field(default=None, alias="foundationalWindowsEnabled")
    foundational_windows: list[WindowItem] | None = Field(default=None, alias="foundationalWindows")


class SumpPump(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    action: str | None = Field(default=None, alias="action")
    hp: str | None = Field(default=None, alias="hp")
    f9_note: str | None = Field(default=None, alias="f9Note")


class FoundationWaterHeater(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    tankless: bool | None = Field(default=None, alias="tankless")
    type: str | None = Field(default=None, alias="type")
    size: str | None = Field(default=None, alias="size")
    rating: str | None = Field(default=None, alias="rating")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")


class WaterSoftener(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    size: str | None = Field(default=None, alias="size")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")


class FoundationBoiler(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    action: str | None = Field(default=None, alias="action")
    f9_note: str | None = Field(default=None, alias="f9Note")
    expansion_tank: bool | None = Field(default=None, alias="expansionTank")
    circulator_pump: bool | None = Field(default=None, alias="circulatorPump")
    oil_tank_replacement: bool | None = Field(default=None, alias="oilTankReplacement")
    oil_replacement: bool | None = Field(default=None, alias="oilReplacement")
    btu: str | None = Field(default=None, alias="btu")
    mbh: str | None = Field(default=None, alias="mbh")


class FoundationBaseboardHeat(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    type: str | None = Field(default=None, alias="type")
    size: str | None = Field(default=None, alias="size")
    action: str | None = Field(default=None, alias="action")


class FoundationHvac(BaseModel):
    model_config = _EE
    air_handlers: list[FoundationAirHandlerRow] | None = Field(default=None, alias="airHandlers")
    furnace: FoundationFurnace | None = Field(default=None, alias="furnace")
    boiler: FoundationBoiler | None = Field(default=None, alias="boiler")
    baseboard_heat: FoundationBaseboardHeat | None = Field(default=None, alias="baseboardHeat")


class Basement(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    wall_clean_pf: str | None = Field(default=None, alias="wallCleanPf")
    muck: bool | None = Field(default=None, alias="muck")
    muck_heavy: bool | None = Field(default=None, alias="muckHeavy")
    drywall_enabled: bool | None = Field(default=None, alias="drywallEnabled")
    drywall_measure_type: MeasureType | None = Field(default=None, alias="drywallMeasureType")
    drywall_value: str | None = Field(default=None, alias="drywallValue")
    stair_cleaning: bool | None = Field(default=None, alias="stairCleaning")
    stair_count: str | None = Field(default=None, alias="stairCount")
    tread_width: str | None = Field(default=None, alias="treadWidth")
    stringers_length: str | None = Field(default=None, alias="stringersLength")
    foundation_door: bool | None = Field(default=None, alias="foundationDoor")
    foundation_door_action: str | None = Field(default=None, alias="foundationDoorAction")
    foundation_windows: list[FoundationWindowRow] | None = Field(default=None, alias="foundationWindows")


class FoundationBreakerPanel(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    amps: str | None = Field(default=None, alias="amps")
    arc_faults: bool | None = Field(default=None, alias="arcFaults")
    panel_replacement: bool | None = Field(default=None, alias="panelReplacement")
    circuit_replacement: bool | None = Field(default=None, alias="circuitReplacement")
    panel_type: str | None = Field(default=None, alias="panelType")
    circuits: list[CircuitRow] | None = Field(default=None, alias="circuits")


class FoundationHouseRewire(BaseModel):
    model_config = _EE
    enabled: bool | None = Field(default=None, alias="enabled")
    home_sf: str | None = Field(default=None, alias="homeSf")


class FoundationElectrical(BaseModel):
    model_config = _EE
    outlets_110: str | None = Field(default=None, alias="outlets110")
    outlets_220: str | None = Field(default=None, alias="outlets220")
    gfi_outlets: str | None = Field(default=None, alias="gfiOutlets")
    light_switch: str | None = Field(default=None, alias="lightSwitch")
    junction_box: str | None = Field(default=None, alias="junctionBox")
    breaker_panel: FoundationBreakerPanel | None = Field(default=None, alias="breakerPanel")
    meter_box: bool | None = Field(default=None, alias="meterBox")
    meter_box_qty: str | None = Field(default=None, alias="meterBoxQty")
    meter_box_size: str | None = Field(default=None, alias="meterBoxSize")
    house_rewire: FoundationHouseRewire | None = Field(default=None, alias="houseRewire")


class FoundationStairs(BaseModel):
    model_config = _EE
    stairs_for_replacement: str | None = Field(default=None, alias="stairsForReplacement")
    size_of_treads: str | None = Field(default=None, alias="sizeOfTreads")
    risers: bool | None = Field(default=None, alias="risers")
    risers_qty: str | None = Field(default=None, alias="risersQty")
    stringers_length: str | None = Field(default=None, alias="stringersLength")
    landing_replacement: bool | None = Field(default=None, alias="landingReplacement")


class Foundation(BaseModel):
    model_config = _EE
    crawlspace: FoundationCrawlspace | None = Field(default=None, alias="crawlspace")
    enclosure_removal: EnclosureRemoval | None = Field(default=None, alias="enclosureRemoval")
    insulation: FoundationInsulation | None = Field(default=None, alias="insulation")
    subgrade_area_coverage: SubgradeAreaCoverage | None = Field(default=None, alias="subgradeAreaCoverage")
    sump_pump: SumpPump | None = Field(default=None, alias="sumpPump")
    water_heater: FoundationWaterHeater | None = Field(default=None, alias="waterHeater")
    water_softener: WaterSoftener | None = Field(default=None, alias="waterSoftener")
    hvac: FoundationHvac | None = Field(default=None, alias="hvac")
    basement: Basement | None = Field(default=None, alias="basement")
    electrical: FoundationElectrical | None = Field(default=None, alias="electrical")
    stairs: FoundationStairs | None = Field(default=None, alias="stairs")
    elevator: bool | None = Field(default=None, alias="elevator")


class ExpressEstimatePayload(BaseModel):
    model_config = _EE
    project_details: ProjectDetails = Field(alias="projectDetails")
    exterior: Exterior | None = Field(default=None, alias="exterior")
    foundation: Foundation | None = Field(default=None, alias="foundation")
    rooms: list[Room] | None = Field(default=None, alias="rooms")
