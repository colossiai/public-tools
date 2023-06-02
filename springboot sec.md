```java
package io.cruiser.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.SecurityFilterChain;

@Configuration // 不能漏
@EnableWebSecurity // 不能漏
public class WebSecurity {
  @Value("${login.users}") private String loginUsers;

  ObjectMapper mapper = new ObjectMapper();

  @Bean // 不能漏
  public SecurityFilterChain configure(HttpSecurity http) throws Exception {
    http.cors()
        .and()
        .csrf()
        .disable()
        .authorizeHttpRequests(x
                               -> x.requestMatchers("/", "/home") // 按顺序， "/", "/home"允许匿名访问
                                      .permitAll()
                                      .anyRequest() // 其他需要登陆才能访问
                                      .authenticated())
        .formLogin();
    return http.build();
  }

  @Bean
  public InMemoryUserDetailsManager userDetailsService() {
    System.out.println("loginUsers str length = " + loginUsers.length());

    List<UserDetails> loginList = new LinkedList<>();
    try {
      Map<String, String> map = mapper.readValue(loginUsers, Map.class);
      for (var entry : map.entrySet()) {
        System.out.println("Add loin user: " + entry.getKey());
        UserDetails user = User.withDefaultPasswordEncoder()
                               .username(entry.getKey())
                               .password(entry.getValue())
                               .roles("USER")
                               .build();
        loginList.add(user);
      }
    } catch (Exception ex) {
      ex.printStackTrace();
    }

    return new InMemoryUserDetailsManager(loginList);
  }
}
```
