# Smart Greenhouse Automation System

A comprehensive, open-source platform for smart greenhouse automation, integrating IoT sensor nodes, automated irrigation, real-time analytics, and advanced protocols to optimize resource usage and improve crop health.

## Features

- Distributed wireless sensor nodes (ESP32)
- Automated irrigation and climate control
- Real-time data analytics and visualization (FastAPI, TimescaleDB, Grafana)
- Secure, scalable, and modular architecture
- Open-source hardware and software

## Repository Structure

- `plantSensorDemo/` — Embedded firmware and hardware for sensor nodes
- `server/` — Backend, database, and deployment scripts
- `images/` — System diagrams and dashboard screenshots
- `greenhouse_report.tex` — Project report and documentation

## Quick StartF

1. **Clone the repository:**

   If you need node firmware or hardware information, clone with submodules:

   ```sh
   git clone --recurse-submodules https://github.com/AzamkhonKh/smart-greenhouse.git
   cd smart-greenhouse
   ```

   Otherwise, for a basic clone:

   ```sh
   git clone https://github.com/AzamkhonKh/smart-greenhouse.git
   cd smart-greenhouse
   ```

2. **Review the [server/README.md](server/README.md)** for backend setup and deployment instructions.
3. **Review the [plantSensorDemo/README.md](plantSensorDemo/README.md)** for sensor node firmware and hardware setup.

## Documentation

- Full system documentation and report: `greenhouse_report.tex`
- Hardware schematics and bill of materials: see `plantSensorDemo/`
- API and backend details: see `server/`

## Contributing

Contributions are welcome! Please open issues or pull requests for improvements, bug fixes, or new features.

## License

MIT License. See [LICENSE](LICENSE) for details.

## References

- [Project Report (PDF)](greenhouse_report.pdf)
- [Grafana](https://grafana.com/)
- [TimescaleDB](https://www.timescale.com/)
- [ESP-IDF](https://docs.espressif.com/projects/esp-idf/en/latest/)

---
For questions or support, please contact the repository maintainer or open an issue.
