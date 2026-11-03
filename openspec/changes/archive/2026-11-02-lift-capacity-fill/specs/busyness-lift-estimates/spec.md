# Spec Delta

## Purpose

Find each lift's capacity and ride speed from the best evidence the data has about it (recorded values, seats, its name, its type), so the busyness model can treat an old two-seat chair and a new eight-seat detachable differently. Rationale and evidence: [decision 013](../../../docs/decisions/013-fill-lift-capacity-and-speed.md).

## ADDED Requirements

### Requirement: Recorded values come first
A lift's recorded capacity SHALL be used when it's between 100 and 6,000 an hour (`CAP_RANGE`), and its recorded ride time when it's between 30 and 2,400 s (`DURATION_RANGE`). A value outside its range SHALL be treated as missing. Only a missing capacity or ride time SHALL be estimated.

#### Scenario: A lift with a recorded capacity but no ride time
- **WHEN** a chairlift records 2,400 an hour and no ride time
- **THEN** it carries 2,400 an hour
- **AND** only its speed is estimated

#### Scenario: An implausible recorded capacity
- **WHEN** a lift records a capacity of 32,200 an hour
- **THEN** its capacity is estimated as if none were recorded

### Requirement: Seats from the data or the name
A lift's seats SHALL be its recorded seats or, if none, the seat count its name gives (TSD6, 4er, Quad, Triple, Double, Pair and their equivalents in other languages). Seats outside 1 to a maximum for the lift type (`SEATS_MAX`: chairlifts 8, gondolas 40, cable cars 250; types not listed 2) SHALL be treated as missing.

#### Scenario: Seats from a name
- **WHEN** a chairlift records no seats and is called "Summit Quad"
- **THEN** it has 4 seats

#### Scenario: Recorded seats win over the name
- **WHEN** a chairlift records 3 seats and its name says Quad
- **THEN** it has 3 seats

#### Scenario: Capacity typed into the seats
- **WHEN** a platter records 720 seats
- **THEN** it has no seats

#### Scenario: A lift maker's name is not a seat count
- **WHEN** a chairlift's name contains "Doppelmayr"
- **THEN** its name gives no seat count

### Requirement: Fast names
A lift's name SHALL mark it as fast when it says so: express, high speed, a detachable code (TSD, KSB, CLD, TCD), "detachable" in French or German, or the Japanese for high speed.

#### Scenario: An express chairlift
- **WHEN** a chairlift is called "Ridge Express"
- **THEN** it is marked fast

### Requirement: Chairlifts by seats
A chairlift with seats and no recorded capacity SHALL take the capacity for its seats and whether its name is fast (`CHAIR_CAP`). With no recorded ride time, it SHALL take the speed for its seats and whether it's at least 1,000 m long (`LONG_M`, `CHAIR_SPEED`).

#### Scenario: A short two-seater
- **WHEN** a 600 m two-seat chairlift records no capacity and no ride time
- **THEN** it carries the two-seat capacity from `CHAIR_CAP`, well under the 2,000 an hour typical of all chairlifts
- **AND** it rides at the short two-seat speed from `CHAIR_SPEED`

#### Scenario: A long six-seater
- **WHEN** a 1,800 m six-seat chairlift records no ride time
- **THEN** it rides at the long six-seat speed from `CHAIR_SPEED`, about twice the 2.5 m/s typical of all chairlifts

#### Scenario: A fast-named quad
- **WHEN** two four-seat chairlifts record no capacity, and only one has a fast name
- **THEN** the fast-named one carries more

### Requirement: Gondolas by seats
A gondola with seats and no recorded capacity SHALL take the capacity for its seats (`GONDOLA_CAP`). Its speed SHALL be the typical gondola speed. A cable car with fewer than 11 seats (`CABLE_MIN_SEATS`) SHALL be treated as a gondola.

#### Scenario: A four-seat gondola
- **WHEN** a four-seat gondola records no capacity
- **THEN** it carries the four-seat capacity from `GONDOLA_CAP`, well under the 2,200 an hour typical of all gondolas

#### Scenario: A small cable car
- **WHEN** a lift tagged as a cable car has 8 seats and no recorded capacity
- **THEN** it carries the eight-seat gondola capacity

### Requirement: Cable cars by cabin size and length
A cable car with 11 or more seats and no recorded capacity SHALL carry its seats × 3,600 ÷ (its length ÷ 8.5 m/s (`CABLE_SPEED`) + 140 s (`CABLE_LOAD_S`)) an hour: one cabin each way per trip, plus loading.

#### Scenario: A long cable car
- **WHEN** a 100-seat cable car 2,500 m long records no capacity
- **THEN** it carries 100 × 3,600 ÷ (2,500 ÷ 8.5 + 140) ≈ 830 an hour

#### Scenario: A short cable car with the same cabins
- **WHEN** a 100-seat cable car is 1,000 m long
- **THEN** it carries more than the 2,500 m one

### Requirement: Type values as the last resort
A lift whose capacity or speed isn't recorded and can't be estimated from seats SHALL take the typical value for its type (`CAP_BY_TYPE`, `LIFT_SPEED`). That SHALL include every lift without seats, every lift type not named above, and any seat count with no entry in its table.

#### Scenario: A T-bar
- **WHEN** a T-bar records no capacity
- **THEN** it carries 1,000 an hour

#### Scenario: A chairlift with no seats
- **WHEN** a chairlift records neither capacity nor seats, and its name gives no seat count
- **THEN** it carries 2,000 an hour at 2.5 m/s

#### Scenario: An unusual seat count
- **WHEN** a gondola with 22 seats records no capacity, and `GONDOLA_CAP` has no 22-seat entry
- **THEN** it carries 2,200 an hour

### Requirement: Ride time from speed
A lift's ride time SHALL be its recorded ride time or, if it has none, its length ÷ its speed.

#### Scenario: A lift with an estimated speed
- **WHEN** a 1,500 m lift has no recorded ride time and a speed of 5 m/s
- **THEN** its ride time is 300 s

### Requirement: Each lift records where its values came from
Each lift in the structure file SHALL record the source of its capacity and of its speed: `recorded`, `seats` (recorded seats), `name` (seats from its name) or `type`.

#### Scenario: A chairlift with seats from its name
- **WHEN** a chairlift's capacity comes from seats read from its name, and its ride time is recorded
- **THEN** its capacity source is `name` and its speed source is `recorded`

### Requirement: Tables are fixed parameters
The tables and constants above SHALL be fixed parameters of the model, changed only deliberately. A new download of the data SHALL change a lift's estimate only if that lift's own data changed.

#### Scenario: A new download
- **WHEN** the data is downloaded again and a lift's type, seats, name and length are unchanged
- **THEN** its estimated capacity and speed are unchanged
