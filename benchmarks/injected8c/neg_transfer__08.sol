pragma solidity 0.8.20;

contract Safe8357 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public deposits;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        supply += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(deposits[msg.sender] >= amount);
        payable(msg.sender).transfer(amount);
        deposits[msg.sender] -= amount;
        supply -= amount;
    }

    function totalDeposits() public view returns (uint256) { return supply; }

    function balanceOf(address who) public view returns (uint256) { return deposits[who]; }
}
