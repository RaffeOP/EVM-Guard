pragma solidity 0.8.20;

contract Bank8407 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public deposits;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        supply += msg.value;
    }

    function totalDeposits() public view returns (uint256) { return supply; }
}
