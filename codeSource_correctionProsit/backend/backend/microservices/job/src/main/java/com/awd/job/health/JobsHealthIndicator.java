package com.awd.job.health;

import com.awd.job.repository.CategoryRepository;
import com.awd.job.repository.JobRepository;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

@Component
public class JobsHealthIndicator implements HealthIndicator {

    private final JobRepository jobRepository;
    private final CategoryRepository categoryRepository;

    public JobsHealthIndicator(JobRepository jobRepository, CategoryRepository categoryRepository) {
        this.jobRepository = jobRepository;
        this.categoryRepository = categoryRepository;
    }

    @Override
    public Health health() {
        try {
            long jobs = jobRepository.count();
            long categories = categoryRepository.count();
            return Health.up()
                    .withDetail("jobs", jobs)
                    .withDetail("categories", categories)
                    .build();
        } catch (Exception e) {
            return Health.down(e)
                    .withDetail("reason", "Cannot read the job tables")
                    .build();
        }
    }
}