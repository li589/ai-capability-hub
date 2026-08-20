# modern-java Modernization Report
### spring-petclinic · Generated 2026-02-21

---

## Project Snapshot

| Property | Value |
|---|---|
| **Application** | Spring PetClinic |
| **Java Version** | 17 |
| **Spring Boot** | 4.0.1 |
| **Files Scanned** | 30 production `.java` files |
| **Reference files loaded** | `01-java8-11.md`, `02-java12-17.md` |
| **Patterns Found** | 6 across 4 files |
| **Estimated Lines Saved** | ~25 |

---

## What's Already Modern ✅

Credit where it's due — the PetClinic already uses:

- `Optional` + `.orElseThrow()` in `OwnerController` (Java 8)
- Stream API with `Comparator.comparing()` in `Vet.getSpecialties()` (Java 8)
- `LocalDate` everywhere — no `java.util.Date` in sight (Java 8)
- Constructor injection throughout — no field `@Autowired`
- Jakarta EE namespace — fully migrated from `javax.*`

---

## Findings

---

### 🔴 Finding 1 — `collect(Collectors.toList())` → `.toList()`
**File:** `vet/Vet.java:63` · **Min version:** Java 16

**BEFORE:**
```java
public List<Specialty> getSpecialties() {
    return getSpecialtiesInternal().stream()
        .sorted(Comparator.comparing(NamedEntity::getName))
        .collect(Collectors.toList());   // ← verbose, mutable, extra import
}
```

**AFTER:**
```java
public List<Specialty> getSpecialties() {
    return getSpecialtiesInternal().stream()
        .sorted(Comparator.comparing(NamedEntity::getName))
        .toList();   // ← unmodifiable, no Collectors import needed
}
```

**Benefit:** `.toList()` returns an *unmodifiable* list — a stronger contract than `Collectors.toList()` which silently returns a mutable `ArrayList`. Better API, fewer imports, fewer characters.

---

### 🔴 Finding 2 — For-loop find-or-throw → Stream + `findFirst`
**File:** `owner/PetTypeFormatter.java:54-58` · **Min version:** Java 8

Classic "iterate, return when found, throw if not" — the textbook stream use case.

**BEFORE:**
```java
@Override
public PetType parse(String text, Locale locale) throws ParseException {
    Collection<PetType> findPetTypes = this.types.findPetTypes();
    for (PetType type : findPetTypes) {
        if (Objects.equals(type.getName(), text)) {
            return type;
        }
    }
    throw new ParseException("type not found: " + text, 0);
}
```

**AFTER:**
```java
@Override
public PetType parse(String text, Locale locale) throws ParseException {
    return this.types.findPetTypes().stream()
        .filter(type -> Objects.equals(type.getName(), text))
        .findFirst()
        .orElseThrow(() -> new ParseException("type not found: " + text, 0));
}
```

**Benefit:** Intent is immediate — *find the first match or throw*. No mutable loop state, no early return to trace. −5 lines.

---

### 🔴 Finding 3 — Two for-loops in `Owner.getPet()` → Streams
**File:** `owner/Owner.java:118-143` · **Min version:** Java 8

`Owner` has two overloads of `getPet()` — both manually iterate the pets list with nested `if` checks.

**BEFORE — `getPet(Integer id)`:**
```java
public Pet getPet(Integer id) {
    for (Pet pet : getPets()) {
        if (!pet.isNew()) {
            Integer compId = pet.getId();
            if (Objects.equals(compId, id)) {
                return pet;
            }
        }
    }
    return null;
}
```

**AFTER:**
```java
public Pet getPet(Integer id) {
    return getPets().stream()
        .filter(pet -> !pet.isNew())
        .filter(pet -> Objects.equals(pet.getId(), id))
        .findFirst()
        .orElse(null);
}
```

**BEFORE — `getPet(String name, boolean ignoreNew)`:**
```java
public Pet getPet(String name, boolean ignoreNew) {
    for (Pet pet : getPets()) {
        String compName = pet.getName();
        if (compName != null && compName.equalsIgnoreCase(name)) {
            if (!ignoreNew || !pet.isNew()) {
                return pet;
            }
        }
    }
    return null;
}
```

**AFTER:**
```java
public Pet getPet(String name, boolean ignoreNew) {
    return getPets().stream()
        .filter(pet -> pet.getName() != null && pet.getName().equalsIgnoreCase(name))
        .filter(pet -> !ignoreNew || !pet.isNew())
        .findFirst()
        .orElse(null);
}
```

**Benefit:** Eliminates nested `if` blocks and temp variables. Each filter predicate is independently readable. −12 lines across both methods.

---

### 🟡 Finding 4 — Lazy `null` init → field initializer
**File:** `vet/Vet.java:52-55`, `vet/Vets.java:37-40` · **Min version:** Java 1.0 (but worth fixing)

Both classes guard a collection field with a `null` check instead of initialising at declaration.

**BEFORE (`Vet.java`):**
```java
protected Set<Specialty> getSpecialtiesInternal() {
    if (this.specialties == null) {
        this.specialties = new HashSet<>();
    }
    return this.specialties;
}
```

**AFTER:**
```java
private Set<Specialty> specialties = new HashSet<>();

protected Set<Specialty> getSpecialtiesInternal() {
    return this.specialties;
}
```

**BEFORE (`Vets.java`):**
```java
public List<Vet> getVetList() {
    if (vets == null) {
        vets = new ArrayList<>();
    }
    return vets;
}
```

**AFTER:**
```java
private List<Vet> vets = new ArrayList<>();

public List<Vet> getVetList() {
    return vets;
}
```

**Benefit:** Removes defensive null-check boilerplate. Initialiser runs once, guaranteed. −6 lines.

---

### 🟡 Finding 5 — Raw cast without pattern matching
**File:** `owner/PetValidator.java:38` · **Min version:** Java 16

The `validate()` method receives `Object obj` but immediately raw-casts it.

**BEFORE:**
```java
@Override
public void validate(Object obj, Errors errors) {
    Pet pet = (Pet) obj;   // ← ClassCastException if wrong type slips through
    // ...
}
```

**AFTER:**
```java
@Override
public void validate(Object obj, Errors errors) {
    if (!(obj instanceof Pet pet)) return;  // ← safe guard, pet in scope below
    // ...
}
```

**Benefit:** No `ClassCastException` risk. Pattern variable `pet` is in scope for the rest of the method. Self-documenting guard in one line.

---

## Upgrade Opportunity 🚀 — Java 21 Unlocks More

The codebase targets Java 17 but Spring Boot 4.0+ supports Java 21 LTS. One `pom.xml` change unlocks:

```xml
<java.version>21</java.version>
```

| What | Where in PetClinic | Benefit |
|---|---|---|
| **Virtual threads** | All `@Controller` request handlers | I/O-bound DB calls park instead of blocking OS threads — free throughput boost |
| **Pattern matching switch** | `PetValidator`, type hierarchies | Eliminates if-else instanceof chains |
| **Sequenced collections** | `Owner.getPets()`, `Vet.getSpecialties()` | `getFirst()` / `getLast()` instead of `get(0)` / `get(size-1)` |

---

## Summary

| File | Pattern | Lines Saved |
|---|---|---|
| `vet/Vet.java` | `collect(Collectors.toList())` → `.toList()` | −1 |
| `vet/Vet.java` | Lazy null init → field initializer | −3 |
| `vet/Vets.java` | Lazy null init → field initializer | −3 |
| `owner/PetTypeFormatter.java` | for-loop find → stream + findFirst | −5 |
| `owner/Owner.java` | 2× for-loop search → stream | −12 |
| `owner/PetValidator.java` | Raw cast → pattern matching instanceof | −1 |
| **Total** | **6 patterns, 4 files** | **~−25 lines** |

---

*Generated by [modern-java](https://github.com/ajaywadhara/modern-java) · `npx skills@1.4.1 add ajaywadhara/modern-java`*
