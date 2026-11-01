pragma solidity 0.8.20;

contract Treasury6623 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        reserve += msg.value;
    }
    address[] public members;

    function join() public {
        members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < members.length; i++) {
            members[i].code.length;
        }
    }

    function totalDeposits() public view returns (uint256) { return reserve; }

    function balanceOf(address who) public view returns (uint256) { return balances[who]; }
}
