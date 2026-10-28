# A Beginner's Guide to the Authentication Service

Welcome! This document is designed to be your personal tutor for understanding the authentication code in this project. We'll go through everything step-by-step, explaining the "what," the "how," and the "why." By the end, you should have a much clearer picture of how it all works.

---

## Part 1: The Core Concepts (The "Why")

Before we look at the code, let's understand the main ideas. Modern applications are built on a few key principles and technologies.

### 1. What is Java? (Object-Oriented Programming)

Java is an **Object-Oriented Programming (OOP)** language. Think of it like building with LEGOs.

*   **Class:** A blueprint. For example, a blueprint for a `Car`. It defines properties (like `color`, `speed`) and behaviors (like `startEngine()`, `accelerate()`). In our code, `UserInfo` is a class—a blueprint for a user.
*   **Object:** An actual thing built from a blueprint. If `Car` is the blueprint, a red Ferrari is an object. In our code, when we create a new user, we are creating an `object` of the `UserInfo` class.
*   **Interface:** A contract. It defines a set of methods that a class *must* implement if it agrees to that contract. It's like saying, "Any class that wants to be a `Vehicle` must have a `startEngine()` method." In our code, `UserDetailsService` is an interface from Spring Security. Our `UserDetailsServiceImpl` class *implements* it, promising to provide the functionality Spring Security needs.

### 2. What is Spring Boot? (The Magic Framework)

Spring Boot is a framework that makes building Java web applications much easier. Its two most important concepts are:

*   **Inversion of Control (IoC):** Normally, *you* create objects and manage their lifecycle. With Spring, the framework does it for you. You just tell Spring what you need, and it provides it.
*   **Dependency Injection (DI):** This is how IoC works. If your `TokenController` needs the `JwtService` to work, you don't create it yourself. You just "declare" that you need it, and Spring "injects" it for you. The `@Autowired` annotation is the most common way to do this.

**Key Spring Annotations:**

*   `@Configuration`: Tells Spring, "This class contains configuration settings."
*   `@Bean`: Tells Spring, "This method creates an object (a bean) that you should manage."
*   `@Service`: Marks a class as a business logic component.
*   `@Repository`: Marks a class that talks to the database.
*   `@RestController`: Marks a class that handles web requests and returns data (like JSON).
*   `@Autowired`: Asks Spring to inject a dependency (an object that this class needs).

### 3. What is Spring Security? (The Bouncer)

Spring Security is a sub-project of Spring that handles all security concerns. Think of it as a bouncer at a club.

*   **Authentication:** Verifying who you are (your username and password).
*   **Authorization:** Checking if you have permission to do something (e.g., only admins can access the admin page).
*   **Filters:** Spring Security works by putting a chain of filters in front of your application. Every web request goes through these filters. Our `JwtAuthFilter` is one such custom filter we add to this chain.

### 4. What is JPA? (The Translator)

JPA (Java Persistence API) is a standard that allows us to talk to a database using Java objects instead of writing raw SQL queries.

*   `@Entity`: Marks a Java class as a blueprint for a database table.
*   `@Table(name = "users")`: Specifies the name of the database table.
*   `@Id`: Marks a field as the primary key for that table.
*   `@Column`: Specifies details about a database column.
*   **Relationships (`@OneToOne`, `@ManyToMany`):** These annotations define how different entities are related, just like in a real database.

### 5. What is a JWT? (The Access Pass)

A JSON Web Token (JWT) is a compact and secure way to represent information between two parties. Think of it as a temporary access pass or a ticket. Once you log in, the server gives you a JWT. For every subsequent request you make to a protected part of the site, you show this JWT to prove you are logged in.

A JWT has three parts: Header, Payload (containing user info), and Signature (to verify it hasn't been tampered with).

---

## Part 2: The Code (The "How")

Let's go through each file.

### `pom.xml` or `build.gradle` (The Recipe Book)

This file lists all the "ingredients" (dependencies) our project needs to work, like Spring Web, Spring Security, JPA, and the JWT library. When you build the project, your build tool (Maven or Gradle) downloads all these libraries automatically.

### `entities` Package (The Database Blueprints)

#### `UserInfo.java`

**Purpose:** This class is the blueprint for the `users` table in our database.

```java
@Entity // 1. Tells JPA: This class maps to a database table.
@Data   // 2. Lombok: Automatically creates getters, setters, toString(), etc.
@Table(name = "users") // 3. Specifies the table name.
public class UserInfo {

    @Id // 4. Marks this field as the primary key.
    @Column(name = "user_id") // 5. Maps this field to the 'user_id' column.
    private String userId;

    private String username; // Maps to 'username' column by default.
    private String password; // Maps to 'password' column.

    @ManyToMany(fetch = FetchType.EAGER) // 6. Defines a Many-to-Many relationship.
    @JoinTable( // 7. Configures the special table that links users and roles.
            name = "users_roles",
            joinColumns = @JoinColumn(name = "user_id"),
            inverseJoinColumns = @JoinColumn(name = "role_id")
    )
    private Set<UserRole> roles = new HashSet<>(); // 8. A user can have a 'Set' of roles.
}
```

**Explanation:**
1.  `@Entity`: The most important annotation here. It turns this simple Java class into a database entity.
2.  `@Data`: A shortcut from the Lombok library to avoid writing boilerplate code.
3.  `@Table`: We explicitly name our table `users`. If we didn't, JPA would guess a name, usually `user_info`.
4.  `@Id`: Every database table needs a unique primary key to identify each row.
5.  `@Column`: We explicitly name the column `user_id`.
6.  `@ManyToMany`: This defines the relationship: one user can have many roles, and one role can be assigned to many users. `FetchType.EAGER` means that whenever you load a `UserInfo` object, JPA will *immediately* load its associated roles as well.
7.  `@JoinTable`: A many-to-many relationship requires a third table (a "join table") to link the primary keys of the two related tables. This annotation configures that.
8.  `Set<UserRole>`: In Java, a `Set` is a collection that contains no duplicate elements, which is perfect for managing roles.

#### `UserRole.java` & `RefreshToken.java`

These follow the same principles. `UserRole` is a simple entity for user roles. `RefreshToken` is an entity that has a `@OneToOne` relationship with `UserInfo`, meaning each user has exactly one refresh token.

### `repository` Package (The Database Workers)

#### `UserRepository.java`

**Purpose:** This interface is responsible for all database operations related to `UserInfo`.

```java
@Repository // 1. Marks this as a Spring Data repository.
public interface UserRepository extends CrudRepository<UserInfo, Long> { // 2
    public UserInfo findByUsername(String username); // 3
}
```

**Explanation:**
1.  `@Repository`: Tells Spring that this is a data access component.
2.  `extends CrudRepository<UserInfo, Long>`: This is where the magic happens. By extending `CrudRepository`, we instantly get a whole set of methods for free: `save()`, `findById()`, `findAll()`, `delete()`, etc. We specify `UserInfo` (the entity it manages) and `Long` (the type of the primary key).
3.  `findByUsername(String username)`: This is a custom query method. Spring Data JPA is smart enough to automatically generate the correct database query just from the method name. This method will find a user by their `username` field.

### `service` Package (The Brains)

#### `JwtService.java`

**Purpose:** All logic for creating, parsing, and validating JWTs lives here.

```java
@Service // Marks this as a service component.
public class JwtService {

    public static final String SECRET = "..."; // A secret key for signing tokens.

    // Extracts the username from a token.
    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    // Validates if the token is correct and not expired.
    public Boolean validateToken(String token, UserDetails userDetails) {
        final String username = extractUsername(token);
        return (username.equals(userDetails.getUsername()) && !isTokenExpired(token));
    }

    // Generates a new JWT for a given username.
    public String GenerateToken(String username){
        Map<String, Object> claims = new HashMap<>();
        return createToken(claims, username);
    }

    // Private helper method to build the token.
    private String createToken(Map<String, Object> claims, String username) {
        return Jwts.builder() // Uses the jjwt library.
                .setClaims(claims)
                .setSubject(username) // The main subject is the username.
                .setIssuedAt(new Date(System.currentTimeMillis()))
                .setExpiration(new Date(System.currentTimeMillis() + 1000 * 60 * 1)) // Set to expire in 1 minute.
                .signWith(getSignKey(), SignatureAlgorithm.HS256).compact(); // Sign it with the secret key.
    }
    // ... other helper methods
}
```

#### `UserDetailsServiceImpl.java`

**Purpose:** This is the bridge between our application's user model (`UserInfo`) and Spring Security's user model (`UserDetails`).

```java
@Service
public class UserDetailsServiceImpl implements UserDetailsService { // 1

    // Dependencies injected by Spring
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    // Constructor for dependency injection
    public UserDetailsServiceImpl(UserRepository u, PasswordEncoder p) {
        this.userRepository = u;
        this.passwordEncoder = p;
    }

    @Override // 2
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        UserInfo user = userRepository.findByUsername(username); // 3
        if (user == null) {
            throw new UsernameNotFoundException("Could not find user: " + username);
        }
        return new CustomUserDetails(user); // 4
    }

    public Boolean signupUser(UserInfoDto userInfoDto) {
        // Check if user already exists
        if (userRepository.findByUsername(userInfoDto.getUsername()) != null) {
            return false;
        }
        // Create a new UserInfo entity
        UserInfo user = new UserInfo();
        user.setUserId(UUID.randomUUID().toString());
        user.setUsername(userInfoDto.getUsername());
        // IMPORTANT: Always encode the password!
        user.setPassword(passwordEncoder.encode(userInfoDto.getPassword()));
        user.setRoles(new HashSet<>());
        // Save the new user to the database
        userRepository.save(user);
        return true;
    }
}
```

**Explanation:**
1.  `implements UserDetailsService`: This class fulfills the `UserDetailsService` contract required by Spring Security.
2.  `@Override`: This is a Java annotation indicating that this method is overriding a method from the interface it implements.
3.  `userRepository.findByUsername(username)`: It uses the repository to find the user in the database.
4.  `return new CustomUserDetails(user)`: It doesn't return our `UserInfo` object directly. Instead, it wraps it in a `CustomUserDetails` object (an adapter class) which Spring Security can understand.

### `auth` Package (The Security Guards)

#### `SecurityConfig.java`

**Purpose:** The main configuration file for Spring Security. This is where we tell the "bouncer" the rules.

```java
@Configuration
@EnableMethodSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http, JwtAuthFilter jwtAuthFilter) throws Exception {
        return http
                .csrf(AbstractHttpConfigurer::disable) // 1. Disable CSRF (common for stateless APIs)
                .authorizeHttpRequests(auth -> auth
                        // 2. List the public URLs that anyone can access.
                        .requestMatchers("/auth/v1/login", "/auth/v1/refreshToken", "/auth/v1/signup").permitAll()
                        // 3. Any other URL requires authentication.
                        .anyRequest().authenticated()
                )
                // 4. We are using a stateless session; don't create a server session.
                .sessionManagement(sess -> sess.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                // 5. Add our custom JWT filter to the security chain.
                .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class)
                .build();
    }
    // ... other beans like PasswordEncoder, AuthenticationManager, etc.
}
```

#### `JwtAuthFilter.java`

**Purpose:** A custom filter that runs on every request to check for and validate a JWT.

```java
@Component
public class JwtAuthFilter extends OncePerRequestFilter { // 1

    @Autowired private JwtService jwtService;
    @Autowired private UserDetailsServiceImpl userDetailsService;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) {
        // 2. Get the "Authorization" header.
        String authHeader = request.getHeader("Authorization");
        // 3. Check if it's a Bearer token.
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7); // Extract the token string.
            String username = jwtService.extractUsername(token); // Get username from token.

            // 4. If token is valid, set the user as authenticated for this request.
            if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
                UserDetails userDetails = userDetailsService.loadUserByUsername(username);
                if (jwtService.validateToken(token, userDetails)) {
                    // Create authentication token
                    UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
                    // Set it in the security context
                    SecurityContextHolder.getContext().setAuthentication(authToken);
                }
            }
        }
        // 5. Continue the filter chain.
        filterChain.doFilter(request, response);
    }
}
```

**Explanation:**
1.  `extends OncePerRequestFilter`: Guarantees this filter only runs once per request.
2.  It looks for the `Authorization` header, which is the standard place to put a token.
3.  It expects the format `Bearer <token>`.
4.  This is the core logic: if the token is valid, it tells Spring Security, "For this one request, this user is logged in." It does this by creating an `Authentication` object and putting it in the `SecurityContextHolder`.
5.  It then lets the request continue to its intended destination (the controller).

### `controller` Package (The Traffic Cops)

#### `AuthController.java` & `TokenController.java`

**Purpose:** These classes define the API endpoints for authentication (`/signup`, `/login`, `/refreshToken`).

```java
@RestController // This class handles web requests and returns JSON.
public class AuthController {

    @Autowired private UserDetailsServiceImpl userDetailsService;
    // ... other autowired services

    @PostMapping("auth/v1/signup") // Maps POST requests to this URL to this method.
    public ResponseEntity SignUp(@RequestBody UserInfoDto userInfoDto) { // 1
        try {
            Boolean isSignedUp = userDetailsService.signupUser(userInfoDto); // 2
            if (!isSignedUp) {
                return new ResponseEntity<>("Already Exist", HttpStatus.BAD_REQUEST);
            }
            // ... generate tokens ...
            return new ResponseEntity<>(/* ... tokens ... */, HttpStatus.OK); // 3
        } catch (Exception ex) {
            return new ResponseEntity<>("Error", HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}
```

**Explanation:**
1.  `@RequestBody`: Spring automatically converts the JSON from the request body into a `UserInfoDto` Java object.
2.  It calls the service layer to perform the actual business logic. Controllers should be thin and delegate work to services.
3.  `ResponseEntity`: This is a Spring class that represents the entire HTTP response, including the status code (like `OK` or `BAD_REQUEST`) and the body (the data sent back to the client).

---

## Part 3: The Full Story (The "How it all works together")

### Scenario 1: A New User Signs Up

1.  **Client:** Sends a `POST` request to `http://your-app/auth/v1/signup` with a JSON body: `{ "username": "newuser", "password": "password123" }`.
2.  **Spring:** The request arrives. `SecurityConfig` allows it because `/auth/v1/signup` is in the `permitAll()` list.
3.  **`AuthController`:** The `SignUp` method is called. The JSON is converted into a `UserInfoDto` object.
4.  **`UserDetailsServiceImpl`:** The `signupUser` method is called.
    *   It hashes the password "password123" into something like `$2a$10$...`.
    *   It creates a new `UserInfo` entity object.
    *   It calls `userRepository.save(user)`.
5.  **`UserRepository`:** JPA generates an `INSERT` SQL statement and saves the new user to the `users` table in the database.
6.  **`AuthController`:** Now that the user is saved, it calls `JwtService` and `RefreshTokenService` to generate the initial set of tokens.
7.  **Client:** Receives a response with a `200 OK` status and a JSON body containing the `accessToken` and `refreshToken`.

### Scenario 2: A User Logs In

1.  **Client:** Sends a `POST` request to `http://your-app/auth/v1/login` with `{ "username": "newuser", "password": "password123" }`.
2.  **`TokenController`:** The `AuthenticateAndGetToken` method is called.
3.  **`AuthenticationManager`:** The controller calls `authenticationManager.authenticate(...)`. This is the entry point to Spring Security's authentication process.
4.  **`DaoAuthenticationProvider` (Internal to Spring):**
    *   It calls your `UserDetailsServiceImpl.loadUserByUsername("newuser")` to get the user from the database. This returns the user with the *hashed* password.
    *   It uses the `PasswordEncoder` to hash the *plain-text* password from the login request ("password123").
    *   It compares the two hashes. If they match, authentication is successful. If not, it throws an exception.
5.  **`TokenController`:** Since authentication was successful, the code continues. It generates a new set of access and refresh tokens.
6.  **Client:** Receives the new tokens.

### Scenario 3: An Authenticated User Accesses a Protected Page

1.  **Client:** Sends a `GET` request to `http://your-app/api/some-protected-data`. It includes a header: `Authorization: Bearer <the_access_token>`.
2.  **`JwtAuthFilter`:** This filter runs first.
    *   It sees the `Authorization` header and extracts the token.
    *   It calls `jwtService.validateToken(...)`. The service checks the token's signature and expiration date.
    *   If the token is valid, the filter loads the `UserDetails` and sets the `Authentication` object in the `SecurityContextHolder`.
3.  **Spring Security:** Sees that there is a valid `Authentication` object in the context and allows the request to proceed.
4.  **Your Controller:** The request finally reaches your controller for `/api/some-protected-data`, which executes its logic and returns the data.
5.  **Client:** Receives the data.

---

I hope this detailed guide helps you understand the project. The best way to learn is to read this, then try to modify or add a small feature yourself. Good luck!

**How to Convert this to a Word Document:**

1.  Open this file (`Beginner_Guide_To_Auth_Service.md`) in your IDE.
2.  Copy the entire content.
3.  Open Microsoft Word (or Google Docs).
4.  Paste the content. The formatting (headings, bold text, code blocks) should be preserved reasonably well.
5.  Save the document.
