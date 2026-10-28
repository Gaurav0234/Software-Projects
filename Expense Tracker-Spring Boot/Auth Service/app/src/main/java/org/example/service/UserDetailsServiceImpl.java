package org.example.service;

import org.apache.juli.logging.Log;
import org.apache.juli.logging.LogFactory;
import org.example.entities.UserInfo;
import org.example.model.UserInfoDto;
import org.example.repository.UserRepository;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.HashSet;
import java.util.Objects;
import java.util.UUID;

@Service
public class UserDetailsServiceImpl implements UserDetailsService {

    private static final Log log =
            LogFactory.getLog(UserDetailsServiceImpl.class);

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public UserDetailsServiceImpl(
            UserRepository userRepository,
            PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public UserDetails loadUserByUsername(String username)
            throws UsernameNotFoundException {

        UserInfo user = userRepository.findByUsername(username);

        if (user == null) {
            log.error("Username not found: " + username);
            throw new UsernameNotFoundException(
                    "Could not find user: " + username);
        }

        log.info("User authenticated successfully");
        return new CustomUserDetails(user);
    }

    public UserInfo checkIfUserAlreadyExist(UserInfoDto userInfoDto) {
        return userRepository.findByUsername(userInfoDto.getUsername());
    }

    // Return the userId String on success, null on failure
    public String signupUser(UserInfoDto userInfoDto) {
        userInfoDto.setPassword(passwordEncoder.encode(userInfoDto.getPassword()));
        if (Objects.nonNull(checkIfUserAlreadyExist(userInfoDto))) {
            return null; // Return null if user already exists
        }

        String userId = UUID.randomUUID().toString();
        UserInfo user = new UserInfo();
        user.setUserId(userId);
        user.setUsername(userInfoDto.getUsername());
        user.setPassword(
                passwordEncoder.encode(userInfoDto.getPassword()));
        user.setRoles(new HashSet<>());

        userRepository.save(user);

        return userId; // Return the new userId
    }
}
