#include <iostream>
#include <list>
#include <experimental/filesystem>
#include <fstream>
#include <map>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <armadillo>
#include <omp.h>
#include <cassert>

#include "../../lib/json.hpp"
#include "../exciton_transfer/cnt.h"
#include "../helper/prepare_directory.hpp"
#include "../helper/progress.hpp"
#include "monte_carlo.h"


namespace mc
{

  // high level method to calculate proper scattering table
  monte_carlo::scatt_t monte_carlo::create_scattering_table(nlohmann::json j) {
    assert(j.count("rate type")>0);

    std::string rate_type = j["rate type"].get<std::string>();
    
    epsr = j["relative permittivity"].get<float>();

    std::cout << "\ninitializing scattering table with " << rate_type << "..." << std::endl;


    if (rate_type == "davoody") {

      // get the parent directory for cnts
      std::string parent_directory = j["cnts"]["directory"];
      j["cnts"].erase("directory");
      j["cnts"].erase("comment");

      // create excitons and calculate exciton dispersions
      std::vector<cnt> cnts;
      cnts.reserve(j["cnts"].size()); // this is reservation of space is crucial to ensure we do not move
                                      // cnts, since the move constructor is not implemented yet
      
      for (const auto& j_cnt : j["cnts"]) {
        cnts.emplace_back(cnt(j_cnt, parent_directory));
        cnts.back().calculate_exciton_dispersion();
      };

      chirality_map.resize(cnts.size());
      for(int i = 0; i < size(cnts); i++){
        chirality_map[i] = cnts[i].chirality();
        std::cout << i <<"th tube's chirality: [" << chirality_map[i][0] << ", " << chirality_map[i][1] << "]" << std::endl;
      }

      monte_carlo::scatt_t all_tables(size(cnts));
      for (int i = 0; i < size(cnts); i++) {
        all_tables[i] = std::vector<scattering_struct>(size(cnts));
        for (int k = 0; k < size(cnts); k++) {
          std::experimental::filesystem::path path_ref =_scatter_table_directory.path();
          path_ref /= std::to_string(cnts[i].chirality()[0])+std::to_string(cnts[i].chirality()[1])+std::to_string(cnts[k].chirality()[0])
                     +std::to_string(cnts[k].chirality()[1])+"_"+std::to_string(j["temperature [kelvin]"].get<float>())+"_"+std::to_string(epsr)+"scat_table";

          if (check_scat_tab(path_ref))
            all_tables[i][k] = recovery_scatt_table(j, path_ref,cnts[i], cnts[k]);
          else {
            std::cout<<"table not found!!"<<std::endl;
            all_tables[i][k] = create_davoody_scatt_table(j, cnts[i], cnts[k]);
          }
        }
      }
  
      return all_tables;
    }

    /*if (rate_type == "forster") {
      return create_forster_scatt_table(1.e15, 1.4e9);
    }

    if (rate_type == "wong") {
      return create_forster_scatt_table(1.e13, 1.4e9);
    }*/
    
    throw std::invalid_argument("rate type must be one of the following: \"davoody\", \"forster\", \"wong\". (Only davoody is implemented.)");

  };

  // method reading from scatter table directory and construct scatter table.
  scattering_struct monte_carlo::recovery_scatt_table(nlohmann::json j, std::experimental::filesystem::path path, const cnt& d_cnt, const cnt& a_cnt) {
    path /= "scat_table";

    arma::vec z_shift;
    z_shift.load(std::string(path) + ".z_shift.dat");

    std::cout<<"z_shift loaded!"<<std::endl;

    arma::vec axis_shift_1;
    axis_shift_1.load(std::string(path) + ".axis_shift_1.dat");

    std::cout<<"axis_shift_1 loaded!"<<std::endl;

    arma::vec axis_shift_2;
    axis_shift_2.load(std::string(path) + ".axis_shift_2.dat");

    std::cout<<"axis_shift_2 loaded!"<<std::endl;

    arma::vec theta;
    theta.load(std::string(path) + ".theta.dat");

    std::cout<<"theta loaded!"<<std::endl;

    arma::field<arma::cube> rate(theta.n_elem);
    unsigned i_th=0;
    rate.for_each([&](arma::cube& c){
      c.load(std::string(path) + std::to_string(i_th)+ ".rates.dat");
      i_th++;});

    scattering_struct scat_table(rate,theta,z_shift,axis_shift_1,axis_shift_2, d_cnt.chirality(), a_cnt.chirality(), epsr,
                                 j["temperature [kelvin]"].get<float>());

    std::experimental::filesystem::path path_out =_output_directory.path();
    path_out /= std::to_string(d_cnt.chirality()[0])+std::to_string(d_cnt.chirality()[1])+std::to_string(a_cnt.chirality()[0])
               +std::to_string(a_cnt.chirality()[1])+"_"+std::to_string(j["temperature [kelvin]"].get<float>())
               +"_"+std::to_string(epsr)+"scat_table";
    std::experimental::filesystem::create_directory(path_out);

    scat_table.save_visible(path_out);
    return scat_table;
  }

  // method to calculate scattering rate via davoody et al. method
  scattering_struct monte_carlo::create_davoody_scatt_table(nlohmann::json j, const cnt& d_cnt, const cnt& a_cnt) {
    auto zshift_prop = _json_prop["zshift [m]"];
    arma::vec z_shift = arma::linspace<arma::vec>(zshift_prop[0], zshift_prop[1], zshift_prop[2]);

    auto axis_shift_prop_1 = _json_prop["axis shift 1 [m]"];
    arma::vec axis_shift_1 = arma::linspace<arma::vec>(axis_shift_prop_1[0], axis_shift_prop_1[1], axis_shift_prop_1[2]);

    auto axis_shift_prop_2 = _json_prop["axis shift 2 [m]"];
    arma::vec axis_shift_2 = arma::linspace<arma::vec>(axis_shift_prop_2[0], axis_shift_prop_2[1], axis_shift_prop_2[2]);

    auto theta_prop = _json_prop["theta [degrees]"];
    arma::vec theta = arma::linspace<arma::vec>(theta_prop[0], theta_prop[1], theta_prop[2])*(constants::pi/180);

    arma::field<arma::cube> rate(theta.n_elem);
    rate.for_each([&](arma::cube& c){c.zeros(z_shift.n_elem, axis_shift_1.n_elem, axis_shift_2.n_elem);});

    exciton_transfer ex_transfer(_json_prop, d_cnt, a_cnt);

    ex_transfer.save_atom_locations(_output_directory.path(), {0, 0}, 1.5e-9, 0, ".0_angle");
    ex_transfer.save_atom_locations(_output_directory.path(), {0, 0}, 1.5e-9, constants::pi / 2, ".90_angle");
    ex_transfer.save_atom_locations(_output_directory.path(), {0, 0}, 1.5e-9, constants::pi, ".180_angle");


    #ifdef DEBUG_CHECK_RATES_SYMMETRY
    {
      double zsh = 1.5e-9;
      double ash1 = 0;
      double ash2 = 0;
      
      double th = 0;
      double r = ex_transfer.first_order(zsh, {ash1, ash2}, th, false);
      std::cout << "rate(" << th << ") = " << r << std::endl;

      th = constants::pi;
      r = ex_transfer.first_order(zsh, {ash1, ash2}, th, false);
      std::cout << "rate(" << th << ") = " << r << std::endl;

      std::exit(0);
    }
    #endif

    // progress_bar prog(theta.n_elem*z_shift.n_elem*axis_shift_1.n_elem*axis_shift_2.n_elem,"create davoody scattering table");
    progress_bar prog(theta.n_elem * z_shift.n_elem * axis_shift_1.n_elem * axis_shift_2.n_elem, "create davoody scattering table");

    #pragma omp parallel
    {
      double th, zsh, ash1, ash2;

      #pragma omp for
      for (unsigned i_th = 0; i_th<theta.n_elem; ++i_th) {

        th = theta(i_th);
        for (unsigned i_zsh = 0; i_zsh < z_shift.n_elem; ++i_zsh) {
          zsh = z_shift(i_zsh);
          for (unsigned i_ash1 = 0; i_ash1 < axis_shift_1.n_elem; ++i_ash1) {
            ash1 = axis_shift_1(i_ash1);
            for (unsigned i_ash2 = 0; i_ash2 < axis_shift_2.n_elem; ++i_ash2) {
              ash2 = axis_shift_2(i_ash2);
              // prog.step();
              rate(i_th)(i_zsh, i_ash1, i_ash2) = ex_transfer.first_order(zsh, {ash1, ash2}, th, false);
              
              #pragma omp critical
              {
                prog.step();
              }
            }
          }
        }

      }
    }

    scattering_struct scat_table(rate,theta,z_shift,axis_shift_1,axis_shift_2, d_cnt.chirality(), a_cnt.chirality(), epsr,
                                 j["temperature [kelvin]"].get<float>());

    double max_rate = 0;
    double min_rate = 10e15;
    rate.for_each([&min_rate](arma::cube& c) { min_rate = min_rate < c.min() ? min_rate : c.min(); });
    rate.for_each([&max_rate](arma::cube& c) { max_rate = max_rate > c.max() ? max_rate : c.max(); });
    
    std::cout << std::endl
              << "max rate in davoody scattering table: " << max_rate << " [1/s]" << std::endl
              << "min rate in davoody scattering table: " << min_rate << " [1/s]"
              << std::endl
              << std::endl;

    // std::string filename(_output_directory.path() / "davoody_scat_rates.dat");
    scat_table.save(_scatter_table_directory.path());

    return scat_table;
  };

  // // method to calculate scattering rate via forster method
  // scattering_struct monte_carlo::create_forster_scatt_table(double gamma_0, double r_0) {
  //   auto zshift_prop = _json_prop["zshift [m]"];
  //   arma::vec z_shift = arma::linspace<arma::vec>(zshift_prop[0], zshift_prop[1], zshift_prop[2]);

  //   auto axis_shift_prop_1 = _json_prop["axis shift 1 [m]"];
  //   arma::vec axis_shift_1 = arma::linspace<arma::vec>(axis_shift_prop_1[0], axis_shift_prop_1[1], axis_shift_prop_1[2]);

  //   auto axis_shift_prop_2 = _json_prop["axis shift 2 [m]"];
  //   arma::vec axis_shift_2 = arma::linspace<arma::vec>(axis_shift_prop_2[0], axis_shift_prop_2[1], axis_shift_prop_2[2]);

  //   auto theta_prop = _json_prop["theta [degrees]"];
  //   arma::vec theta = arma::linspace<arma::vec>(theta_prop[0], theta_prop[1], theta_prop[2])*(constants::pi/180);

  //   arma::field<arma::cube> rate(theta.n_elem);
  //   rate.for_each([&](arma::cube& c){c.zeros(z_shift.n_elem, axis_shift_1.n_elem, axis_shift_2.n_elem);});

  //   progress_bar prog(theta.n_elem*z_shift.n_elem*axis_shift_1.n_elem*axis_shift_2.n_elem,"create forster scattering table");

  //   unsigned i_th=0;
  //   for (const auto& th: theta) {
  //     unsigned i_zsh=0;
  //     for (const auto& zsh: z_shift) {
  //       unsigned i_ash1=0;
  //       for (const auto& ash1: axis_shift_1) {
  //         unsigned i_ash2=0;
  //         for (const auto& ash2: axis_shift_2) {
  //           prog.step();
  //           arma::vec r1 = {ash1, 0, 0};
  //           arma::vec r2 = {ash2*std::cos(th), ash2*std::sin(th), zsh};
  //           arma::vec dR = r1-r2;
  //           double angle_factor = std::cos(th)-3*arma::dot(arma::normalise(r1),arma::normalise(dR))*arma::dot(arma::normalise(r2),arma::normalise(dR));
  //           rate(i_th)(i_zsh,i_ash1,i_ash2) = gamma_0*std::pow(angle_factor,2)*std::pow(1.e-9/arma::norm(dR),6);
  //           i_ash2++;
  //         }
  //         i_ash1++;
  //       }
  //       i_zsh++;
  //     }
  //     i_th++;
  //   }

  //   scattering_struct scat_table(rate,theta,z_shift,axis_shift_1,axis_shift_2, nullptr, nullptr);

  //   return scat_table;
  // };

  // slice the domain into n sections in each direction, and return a list of scatterers in the center region as the injection region
  std::vector<const scatterer *> monte_carlo::injection_region(const std::vector<scatterer> &all_scat, const domain_t domain, const int n) {
    assert((n > 0) && (n % 2 == 1));

    double xmin = domain.first(0), ymin = domain.first(1), zmin = domain.first(2);
    double xmax = domain.second(0), ymax = domain.second(1), zmax = domain.second(2);
    double dx = (xmax - xmin) / double(n), dy = (ymax - ymin) / double(n), dz = (zmax - zmin) / double(n);

    std::vector<double> x, y, z;

    for (int i = 0; i <= n; ++i) {
      x.push_back(double(i) * dx + xmin);
      y.push_back(double(i) * dy + ymin);
      z.push_back(double(i) * dz + zmin);
    }

    std::vector<const scatterer *> inject_list;

    for (const auto& s : all_scat) {
      if (x[n / 2] <= s.pos(0) && s.pos(0) <= x[n / 2 + 1] &&
          y[n / 2] <= s.pos(1) && s.pos(1) <= y[n / 2 + 1] &&
          z[n / 2] <= s.pos(2) && s.pos(2) <= z[n / 2 + 1])
        inject_list.push_back(&s);
    }


    return inject_list;
  }

  // slice the domain into n sections in each direction, and return the domain that leaves only 1 section from each side
  monte_carlo::domain_t monte_carlo::get_removal_domain(const monte_carlo::domain_t domain, const int n) {
    assert((n > 1));

    double xmin = domain.first(0), ymin = domain.first(1), zmin = domain.first(2);
    double xmax = domain.second(0), ymax = domain.second(1), zmax = domain.second(2);
    double dx = (xmax - xmin) / double(n), dy = (ymax - ymin) / double(n), dz = (zmax - zmin) / double(n);

    std::vector<double> x, y, z;

    for (int i = 0; i <= n; ++i) {
      x.push_back(double(i) * dx + xmin);
      y.push_back(double(i) * dy + ymin);
      z.push_back(double(i) * dz + zmin);
    }

    domain_t removal_domain;
    removal_domain.first = {x[1], y[1], z[1]};
    std::cout << "remove domain lower limit:  x: " << x[1] << " , y: " << y[1] << " , z: " << z[1] << std::endl;
    removal_domain.second = {x[n-1], y[n-1], z[n-1]};
    std::cout << "remove domain upper limit:  x: " << x[n-1] << " , y: " << y[n-1] << " , z: " << z[n-1] << std::endl;

    return removal_domain;
  }

  // initialize the simulation condition to calculate diffusion coefficient using green-kubo approach
  void monte_carlo::kubo_init() {
    // set maximum hopping radius
    _max_hopping_radius = double(_json_prop["max hopping radius [m]"]);
    std::cout << "maximum hopping radius: " << _max_hopping_radius * 1.e9 << " [nm]\n";

    _max_dissolving_radius = double(_json_prop["max dissolving radius [m]"]);
    std::cout << "maximum dissolving radius: " << _max_dissolving_radius * 1.e9 << " [nm]\n";

    _particle_velocity = _json_prop["exciton velocity [m/s]"];
    std::cout << "exciton velocity [m/s]: " << _particle_velocity << std::endl;

    _scat_tables = create_scattering_table(_json_prop);
    _all_scat_list = create_scatterers(_input_directory.path());

    domain_t d = find_simulation_domain();
    std::ios::fmtflags f(std::cout.flags()); // save cout flags to be reset after printing
    std::cout << std::fixed << std::showpos;
    std::cout << "\n"
              << "simulation domain BEFORE trimming:\n"
              << "    x (" << d.first(0) * 1e9 << " , " << d.second(0) * 1e9 << ") [nm]\n"
              << "    y (" << d.first(1) * 1e9 << " , " << d.second(1) * 1e9 << ") [nm]\n"
              << "    z (" << d.first(2) * 1e9 << " , " << d.second(2) * 1e9 << ") [nm]\n"
              << std::endl;
    std::cout.flags(f); // reset the cout flags

    limit_t xlim = _json_prop["trim limits"]["xlim"];
    limit_t ylim = _json_prop["trim limits"]["ylim"];
    limit_t zlim = _json_prop["trim limits"]["zlim"];

    trim_scats(xlim, ylim, zlim, _all_scat_list);

    _domain = find_simulation_domain();
    f = std::cout.flags(); // save cout flags to be reset after printing
    std::cout << std::fixed << std::showpos;
    std::cout << "\n"
              << "simulation domain AFTER trimming:\n"
              << "    x (" << _domain.first(0) * 1e9 << " , " << _domain.second(0) * 1e9 << ") [nm]\n"
              << "    y (" << _domain.first(1) * 1e9 << " , " << _domain.second(1) * 1e9 << ") [nm]\n"
              << "    z (" << _domain.first(2) * 1e9 << " , " << _domain.second(2) * 1e9 << ") [nm]\n"
              << std::endl;
    std::cout.flags(f); // reset the cout flags

    std::cout << "total number of scatterers: " << _all_scat_list.size() << std::endl;

    double quenching_density = _json_prop["density of quenching sites"];
    _quenching_sites_num = quenching_density * _all_scat_list.size();
    _quenching_list = create_quenching_sites(_all_scat_list, _quenching_sites_num);
    std::cout << "total number of quenching sites: " << _quenching_list.size() << std::endl;
    set_scat_tables(_scat_tables,chirality_map, _all_scat_list);

    create_scatterer_buckets(_domain, _max_hopping_radius, _all_scat_list, _scat_buckets, _quenching_list, _q_buckets);
    set_max_rate(_max_hopping_radius, _all_scat_list);

    int n = _json_prop["number of sections for injection region"];
    _inject_scats = injection_region(_all_scat_list, _domain, n);
    _removal_domain = get_removal_domain(_domain, n);

    _max_time = _json_prop["maximum time for kubo simulation [seconds]"];
  };

  // create particles for kubo simulation
  void monte_carlo::kubo_create_particles() {
    int n_particle = _json_prop["number of particles for kubo simulation"];
    for (int i=0; i<n_particle; ++i) {
      int dice = std::rand() % _inject_scats.size();
      const scatterer *s = _inject_scats[dice];
      arma::vec pos = s->pos();
      _particle_list.push_back(particle(pos, s, _particle_velocity));
      _particle_list.back().set_init_pos(pos);
    }
  }

  // step the simulation in time
  void monte_carlo::kubo_step(double dt) {
    #pragma omp parallel
    {
      #pragma omp for
      for (unsigned i = 0; i < _particle_list.size(); ++i) {
        particle& p = _particle_list[i];
        
        p.step(dt, _all_scat_list, _max_hopping_radius, _max_dissolving_radius);
        
        p.update_delta_pos();

        if (arma::any(p.pos()<_removal_domain.first) || arma::any(_removal_domain.second < p.pos())){
         // std::cout << "remove particles at:  x: " << p.pos()[0] << " , y: " << p.pos()[1] << " , z: " << p.pos()[2];
          const scatterer* old_scat = p.scat_ptr();
          bool condition = true;
          const scatterer* s = nullptr;
        // std::cout << "chiral" << old_scat->chirality()[0] << "," << old_scat->chirality()[1] << ",";
          do {
            int dice = std::rand() % _inject_scats.size();
            s = _inject_scats[dice];
            const arma::vec old_chiral = old_scat->chirality();
            const arma::vec new_chiral = s->chirality();
            condition = arma::any(old_chiral != new_chiral);
          } while (condition);
          arma::vec pos = s->pos();
          p.set_pos(pos);
          p.set_old_pos(pos);
          // p.update_past_delta_pos();  add total displacement of last journey to past delta pos
          p.set_scatterer(s);
         // std::cout << "to:  x: " << p.pos()[0] << " , y: " << p.pos()[1] << " , z: " << p.pos()[2];
          // std::cout << "chiral" << s->chirality()[0] << "," << s->chirality()[1] << "," << std::endl;
        }
      }
    }

    // increase simulation time
    _time += dt;
  };

  // save the displacement of individual particles in kubo simulation
  void monte_carlo::kubo_save_individual_particle_displacements() {
    if (! _displacement_file_x.is_open()) {
      _displacement_file_x.open(_output_directory.path() / "particle_displacement.x.dat", std::ios::out);
      _displacement_file_y.open(_output_directory.path() / "particle_displacement.y.dat", std::ios::out);
      _displacement_file_z.open(_output_directory.path() / "particle_displacement.z.dat", std::ios::out);

      _displacement_file_x << std::showpos << std::scientific;
      _displacement_file_y << std::showpos << std::scientific;
      _displacement_file_z << std::showpos << std::scientific;

      _displacement_file_x << "time";
      _displacement_file_y << "time";
      _displacement_file_z << "time";
      for (int i=0; i<int(_particle_list.size()); ++i){
        _displacement_file_x << "," << i;
        _displacement_file_y << "," << i;
        _displacement_file_z << "," << i;
      }
      _displacement_file_x << std::endl;
      _displacement_file_y << std::endl;
      _displacement_file_z << std::endl;
    }

    _displacement_file_x << time();
    _displacement_file_y << time();
    _displacement_file_z << time();

    for (const auto& p: _particle_list) {
      _displacement_file_x << "," << p.delta_pos(0);
      _displacement_file_y << "," << p.delta_pos(1);
      _displacement_file_z << "," << p.delta_pos(2);
    }
    _displacement_file_x << std::endl;
    _displacement_file_y << std::endl;
    _displacement_file_z << std::endl;
  };

  // save the displacement of individual particles in kubo simulation
  void monte_carlo::kubo_save_individual_particle_positions() {
    if (! _position_file_x.is_open()) {
      _position_file_x.open(_output_directory.path() / "particle_position.x.dat", std::ios::out);
      _position_file_y.open(_output_directory.path() / "particle_position.y.dat", std::ios::out);
      _position_file_z.open(_output_directory.path() / "particle_position.z.dat", std::ios::out);

      _position_file_x << std::showpos << std::scientific;
      _position_file_y << std::showpos << std::scientific;
      _position_file_z << std::showpos << std::scientific;

      _position_file_x << "time";
      _position_file_y << "time";
      _position_file_z << "time";
      for (int i=0; i<int(_particle_list.size()); ++i){
        _position_file_x << "," << i;
        _position_file_y << "," << i;
        _position_file_z << "," << i;
      }
      _position_file_x << std::endl;
      _position_file_y << std::endl;
      _position_file_z << std::endl;
    }

    _position_file_x << time();
    _position_file_y << time();
    _position_file_z << time();

    for (const auto& p: _particle_list) {
      _position_file_x << "," << p.pos(0);
      _position_file_y << "," << p.pos(1);
      _position_file_z << "," << p.pos(2);
    }
    _position_file_x << std::endl;
    _position_file_y << std::endl;
    _position_file_z << std::endl;
  };

  void monte_carlo::kubo_save_avg_displacement_squared() {
    if (!_displacement_squard_file.is_open()) {
      _displacement_squard_file.open(_output_directory.path() / "particle_displacement.avg.squared.dat", std::ios::out);

      _displacement_squard_file << std::showpos << std::scientific;
      
      _displacement_squard_file << "# this file contains the average of dx^2, dy^2, and dz^2 of the particle ensemble over time" << std::endl
                                << "# number of particles: " << _particle_list.size() << std::endl
                                << std::endl;

      _displacement_squard_file << "time,x,y,z" << std::endl;
    }

    
    double avg_x2=0, avg_y2=0, avg_z2=0;

    for (const auto& p : _particle_list) {
      avg_x2 += std::pow(p.delta_pos(0), 2);
      avg_y2 += std::pow(p.delta_pos(1), 2);
      avg_z2 += std::pow(p.delta_pos(2), 2);
    }

    avg_x2 /= double(_particle_list.size());
    avg_y2 /= double(_particle_list.size());
    avg_z2 /= double(_particle_list.size());

    _displacement_squard_file << time() << "," << avg_x2 << "," << avg_y2 << "," << avg_z2 << std::endl;
  }

  void monte_carlo::kubo_save_diffusion_tensor(){
    if (!_diffusion_tensor_file.is_open()) {
      _diffusion_tensor_file.open(_output_directory.path() / "particle_diffusion_tensor.dat", std::ios::out);

     _diffusion_tensor_file << std::showpos << std::scientific;
      
      _diffusion_tensor_file << "# this file contains the diffusion tensor Dij of the particle ensemble over time" << std::endl
                                << "# number of particles: " << _particle_list.size() << std::endl
                                << std::endl;

      _diffusion_tensor_file << "time,Dxx,Dxy,Dxz,Dyy,Dyz,Dzz" << std::endl;
    }

    _diffusion_tensor_file << time();

    double Dij, D1, D2, D3;
    for(int i = 0; i < 3; i++){
      for(int j = i; j < 3; j++){
        D1 = 0; D2 = 0; D3 = 0;
        for(const auto& p : _particle_list){
          D1 += p.delta_pos(i)*p.delta_pos(j);
          D2 += p.delta_pos(i);
          D3 += p.delta_pos(j);
        }
        D1 /= double(_particle_list.size());
        D2 /= double(_particle_list.size());
        D3 /= double(_particle_list.size());
        Dij = (D1 - (D2 * D3))/(2 * time());
        _diffusion_tensor_file << "," << Dij;
      }
    }
    _diffusion_tensor_file << std::endl;
  }

  // TODO: the method currently not available. Error in calculation.
  void monte_carlo::kubo_save_diffusion_length() {
    if (!_diffusion_length_file.is_open()) {
      _diffusion_length_file.open(_output_directory.path() / "particle_diffusion_length.dat", std::ios::out);

      _diffusion_length_file << std::showpos << std::scientific;
      
      _diffusion_length_file << "# this file contains the diffusion length in x,y,z of each particle in the ensemble" << std::endl
                                << "# number of particles: " << _particle_list.size() << std::endl
                                << std::endl;

      _diffusion_length_file << "x,y,z" << std::endl;
    }

    for (const auto& p : _particle_list) {
      _diffusion_length_file << p.diff_len(0) << "," << p.diff_len(1) << "," << p.diff_len(2) << std::endl;
    }
    
  }

  // helper function to check if scatter table is saved.
  bool monte_carlo::check_scat_tab(std::experimental::filesystem::path path_ref){

    for(auto& p: std::experimental::filesystem::directory_iterator(_scatter_table_directory.path())){
        if(p==path_ref)
        return true;
    }
    return false;
  }

  // helper function calculate average scattering time per exciton during the whole simulation
  void monte_carlo::print_exciton_scatter_times(){
    int total =0;
    for (const auto& p : _particle_list){
      total += p.scatter_time();
    }
    std::cout << "average scatter times of exciton is " << (double)total/(double)_particle_list.size() << std::endl;
  }

} // end of namespace mc
