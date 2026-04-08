from app.tools.transit_tools import (
    tool_bus_arrival,
    tool_taxi_availability,
    tool_traffic_incidents,
)

print(tool_bus_arrival("83139", "190"))
print(tool_taxi_availability())
print(tool_traffic_incidents())